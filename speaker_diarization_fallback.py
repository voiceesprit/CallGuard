#!/usr/bin/env python3
"""
Optimized Speaker Diarization Script with Translation
Uses OpenAI Whisper for transcription and optimized processing for speed
"""

import whisper
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings
import torch
from pydub import AudioSegment
import json
import os
from googletrans import Translator
import langdetect
from langdetect import detect, DetectorFactory
import re
import time

# Suppress warnings
warnings.filterwarnings("ignore")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Performance configuration
BATCH_SIZE = 20  # Process segments in batches

@dataclass
class SpeakerSegment:
    """Represents a segment of speech from a speaker"""
    speaker_id: str
    start_time: float
    end_time: float
    text: str
    original_text: str = ""  # Store original text if translated
    detected_language: str = ""  # Store detected language
    is_translated: bool = False  # Flag if text was translated


class AudioTranslator:
    """Handles language detection and translation of audio segments"""
    
    def __init__(self):
        """Initialize the translator"""
        self.translator = Translator()
        self._language_cache = {}  # Cache for language detection results
        
    def detect_language(self, text: str) -> str:
        """Robust language detection using multiple methods with caching"""
        # Check cache first
        text_hash = hash(text.strip().lower())
        if text_hash in self._language_cache:
            return self._language_cache[text_hash]
        
        try:
            if not text.strip():
                return "unknown"
            
            # Clean the text for better detection
            clean_text = self._clean_text_for_detection(text)
            if not clean_text:
                return "unknown"
            
            # Method 1: Use langdetect library (most accurate for longer texts)
            try:
                # Set seed for consistent results
                DetectorFactory.seed = 0
                detected_lang = detect(clean_text)
                confidence = self._get_langdetect_confidence(clean_text, detected_lang)
                
                if confidence > 0.7:  # High confidence threshold
                    logger.debug(f"langdetect detected: {detected_lang} (confidence: {confidence:.2f})")
                    self._language_cache[text_hash] = detected_lang
                    return detected_lang
            except Exception as e:
                logger.debug(f"langdetect failed: {e}")
            
            # Method 2: Enhanced keyword-based detection with more languages
            keyword_lang = self._keyword_based_detection(clean_text)
            if keyword_lang != "unknown":
                logger.debug(f"Keyword detection: {keyword_lang}")
                self._language_cache[text_hash] = keyword_lang
                return keyword_lang
            
            # Method 3: Character pattern analysis
            pattern_lang = self._pattern_based_detection(clean_text)
            if pattern_lang != "unknown":
                logger.debug(f"Pattern detection: {pattern_lang}")
                self._language_cache[text_hash] = pattern_lang
                return pattern_lang
            
            # Method 4: Use Google Translate's language detection as fallback
            try:
                translation = self.translator.translate(clean_text, dest="en")
                detected_lang = translation.src
                if detected_lang != "en":
                    logger.debug(f"Google Translate detected: {detected_lang}")
                    self._language_cache[text_hash] = detected_lang
                    return detected_lang
            except Exception as e:
                logger.debug(f"Google Translate detection failed: {e}")
            
            # Default to English if no other language detected with confidence
            logger.debug("Defaulting to English")
            self._language_cache[text_hash] = "en"
            return "en"
                
        except Exception as e:
            logger.warning(f"Error in language detection: {e}")
            self._language_cache[text_hash] = "unknown"
            return "unknown"
    
    def _clean_text_for_detection(self, text: str) -> str:
        """Clean text for better language detection"""
        # Remove special characters and numbers
        clean_text = re.sub(r'[^\w\s]', ' ', text)
        clean_text = re.sub(r'\d+', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if len(clean_text.split()) < 2:
            return ""
        
        return clean_text
    
    def _get_langdetect_confidence(self, text: str, detected_lang: str) -> float:
        """Get confidence score for langdetect result"""
        try:
            from langdetect import detect_langs
            detections = detect_langs(text)
            
            # Find the confidence for the detected language
            for detection in detections:
                if detection.lang == detected_lang:
                    return detection.prob
            
            return 0.0
        except ImportError:
            logger.warning("langdetect.detect_langs not available, using default confidence")
            return 0.5
        except Exception as e:
            logger.debug(f"Error calculating langdetect confidence: {e}")
            return 0.5  # Default confidence if we can't calculate
    
    def _keyword_based_detection(self, text: str) -> str:
        """Enhanced keyword-based language detection"""
        text_lower = text.lower()
        
        # French keywords (expanded)
        french_words = [
            'bonjour', 'salut', 'merci', 'oui', 'non', 'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
            'avec', 'pour', 'dans', 'sur', 'par', 'de', 'du', 'des', 'le', 'la', 'les', 'un', 'une',
            'être', 'avoir', 'faire', 'aller', 'venir', 'voir', 'savoir', 'pouvoir', 'vouloir'
        ]
        
        # Spanish keywords (expanded)
        spanish_words = [
            'hola', 'gracias', 'por favor', 'sí', 'no', 'yo', 'tú', 'él', 'ella', 'nosotros', 'vosotros', 'ellos', 'ellas',
            'con', 'para', 'en', 'sobre', 'por', 'de', 'del', 'los', 'las', 'el', 'la', 'un', 'una',
            'ser', 'estar', 'tener', 'hacer', 'ir', 'venir', 'ver', 'saber', 'poder', 'querer'
        ]
        
        # German keywords (expanded)
        german_words = [
            'hallo', 'guten tag', 'danke', 'bitte', 'ja', 'nein', 'ich', 'du', 'er', 'sie', 'wir', 'ihr', 'sie',
            'mit', 'für', 'in', 'auf', 'über', 'von', 'der', 'die', 'das', 'ein', 'eine',
            'sein', 'haben', 'machen', 'gehen', 'kommen', 'sehen', 'wissen', 'können', 'wollen'
        ]
        
        # Italian keywords (expanded)
        italian_words = [
            'ciao', 'grazie', 'prego', 'sì', 'no', 'io', 'tu', 'lui', 'lei', 'noi', 'voi', 'loro',
            'con', 'per', 'in', 'su', 'sopra', 'di', 'da', 'il', 'la', 'i', 'gli', 'le', 'un', 'una',
            'essere', 'avere', 'fare', 'andare', 'venire', 'vedere', 'sapere', 'potere', 'volere'
        ]
        
        # Portuguese keywords
        portuguese_words = [
            'olá', 'oi', 'obrigado', 'obrigada', 'por favor', 'sim', 'não', 'eu', 'tu', 'você', 'ele', 'ela',
            'nós', 'vós', 'eles', 'elas', 'com', 'para', 'em', 'sobre', 'de', 'do', 'da', 'o', 'a', 'os', 'as'
        ]
        
        # Dutch keywords
        dutch_words = [
            'hallo', 'dank je', 'alsjeblieft', 'ja', 'nee', 'ik', 'jij', 'hij', 'zij', 'wij', 'jullie', 'zij',
            'met', 'voor', 'in', 'op', 'over', 'van', 'de', 'het', 'een', 'een'
        ]
        
        # Russian keywords
        russian_words = [
            'привет', 'спасибо', 'пожалуйста', 'да', 'нет', 'я', 'ты', 'он', 'она', 'мы', 'вы', 'они',
            'с', 'для', 'в', 'на', 'о', 'от', 'из', 'к', 'по', 'за'
        ]
        
        # Japanese keywords
        japanese_words = [
            'こんにちは', 'ありがとう', 'お願いします', 'はい', 'いいえ', '私', 'あなた', '彼', '彼女', '私たち', 'あなたたち', '彼ら'
        ]
        
        # Chinese keywords
        chinese_words = [
            '你好', '谢谢', '请', '是', '不', '我', '你', '他', '她', '我们', '你们', '他们'
        ]
        
        # Count matches for each language
        language_scores = {
            'fr': sum(1 for word in french_words if word in text_lower),
            'es': sum(1 for word in spanish_words if word in text_lower),
            'de': sum(1 for word in german_words if word in text_lower),
            'it': sum(1 for word in italian_words if word in text_lower),
            'pt': sum(1 for word in portuguese_words if word in text_lower),
            'nl': sum(1 for word in dutch_words if word in text_lower),
            'ru': sum(1 for word in russian_words if word in text_lower),
            'ja': sum(1 for word in japanese_words if word in text_lower),
            'zh': sum(1 for word in chinese_words if word in text_lower)
        }
        
        # Find language with highest score
        max_score = max(language_scores.values())
        if max_score >= 2:  # Require at least 2 keyword matches
            detected_lang = max(language_scores, key=language_scores.get)
            logger.debug(f"Keyword detection: {detected_lang} (score: {max_score})")
            return detected_lang
        
        return "unknown"
    
    def _pattern_based_detection(self, text: str) -> str:
        """Detect language based on character patterns and writing systems"""
        # Check for specific writing systems
        if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text):  # Hiragana/Katakana
            return "ja"
        elif re.search(r'[\u4E00-\u9FFF]', text):  # Chinese characters
            return "zh"
        elif re.search(r'[\uAC00-\uD7AF]', text):  # Korean Hangul
            return "ko"
        elif re.search(r'[\u0600-\u06FF]', text):  # Arabic
            return "ar"
        elif re.search(r'[\u0590-\u05FF]', text):  # Hebrew
            return "he"
        elif re.search(r'[\u0E00-\u0E7F]', text):  # Thai
            return "th"
        elif re.search(r'[\u0C80-\u0CFF]', text):  # Kannada
            return "kn"
        
        # Check for Cyrillic characters (Russian, Bulgarian, Serbian, etc.)
        if re.search(r'[\u0400-\u04FF]', text):
            # Try to determine specific Slavic language
            if any(word in text.lower() for word in ['привет', 'спасибо', 'да', 'нет']):
                return "ru"
            elif any(word in text.lower() for word in ['здравей', 'благодаря', 'да', 'не']):
                return "bg"
            else:
                return "ru"  # Default to Russian for Cyrillic
        
        # Check for Greek characters
        if re.search(r'[\u0370-\u03FF]', text):
            return "el"
        
        # Check for Devanagari (Hindi, Marathi, etc.)
        if re.search(r'[\u0900-\u097F]', text):
            return "hi"
        
        return "unknown"
    
    def get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name from language code"""
        language_names = {
            'en': 'English',
            'fr': 'French',
            'es': 'Spanish',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'nl': 'Dutch',
            'ru': 'Russian',
            'ja': 'Japanese',
            'zh': 'Chinese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'he': 'Hebrew',
            'th': 'Thai',
            'kn': 'Kannada',
            'bg': 'Bulgarian',
            'el': 'Greek',
            'hi': 'Hindi',
            'unknown': 'Unknown'
        }
        return language_names.get(lang_code, lang_code)
    
    def translate_to_english(self, text: str, source_lang: str = None) -> Tuple[str, str, bool]:
        """Translate text to English"""
        try:
            if not text.strip():
                return text, "unknown", False
            
            # If source language not provided, detect it
            if source_lang is None:
                source_lang = self.detect_language(text)
            
            # If already English, no need to translate
            if source_lang == "en" or source_lang == "unknown":
                return text, source_lang, False
            
            lang_name = self.get_language_name(source_lang)
            logger.info(f"Translating from {lang_name} ({source_lang}) to English...")
            
            # Translate using Google Translate
            translation = self.translator.translate(text, src=source_lang, dest="en")
            translated_text = translation.text
            
            logger.info(f"Translation: '{text}' → '{translated_text}'")
            
            return translated_text, source_lang, True
            
        except Exception as e:
            logger.warning(f"Translation failed: {e}")
            return text, source_lang, False

class SimpleDiarizer:
    """High-performance diarizer using Whisper with GPU acceleration and batch processing"""
    
    def __init__(self):
        """Initialize the diarizer"""
        self.model = None
        self.translator = AudioTranslator()
        
    def load_whisper_model(self, model_size: str = "small"):
        """Load Whisper model with minimal overhead"""
        try:
            logger.info(f"Loading Whisper {model_size} model...")
            
            # Simple device detection
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Load model directly with device
            self.model = whisper.load_model(model_size, device=device)
            
            if device == "cuda":
                logger.info("GPU acceleration enabled")
            else:
                logger.info("Using CPU processing")
            
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            raise
    
    def _batch_detect_language(self, texts: List[str]) -> Tuple[str, float]:
        """Fast language detection for multiple texts"""
        try:
            # Combine all texts
            combined_text = " ".join(texts)
            
            # Quick English check first (fastest)
            if self._quick_english_check(combined_text):
                return "en", 1.0
            
            # Simple langdetect (faster than complex detection)
            DetectorFactory.seed = 0
            detected_lang = detect(combined_text)
            
            # If not English, return detected language
            if detected_lang != "en":
                return detected_lang, 0.8
            
            return "en", 0.9
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "en", 0.5
    
    def _quick_english_check(self, text: str) -> bool:
        """Quick heuristic to check if text is likely English"""
        # Common English words that appear frequently
        english_indicators = [
            'the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with',
            'as', 'for', 'this', 'are', 'on', 'be', 'at', 'by', 'i', 'you',
            'have', 'not', 'they', 'he', 'she', 'we', 'my', 'your', 'their',
            'what', 'when', 'where', 'why', 'how', 'can', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall'
        ]
        
        text_lower = text.lower()
        word_count = len(text.split())
        if word_count < 3:
            return False
        
        # Count English indicator words
        english_word_count = sum(1 for word in english_indicators if word in text_lower)
        english_ratio = english_word_count / word_count
        
        # If more than 30% of words are English indicators, likely English
        return english_ratio > 0.3
    
    def _batch_translate_if_needed(self, segments: List[SpeakerSegment], detected_lang: str) -> List[SpeakerSegment]:
        """Batch translate segments if language is not English"""
        if detected_lang == "en":
            logger.info("Audio is in English - skipping translation")
            return segments
        
        logger.info(f"Batch translating {len(segments)} segments from {detected_lang} to English...")
        
        # Collect all texts that need translation
        texts_to_translate = []
        segment_indices = []
        
        for i, segment in enumerate(segments):
            if segment.detected_language != "en":
                texts_to_translate.append(segment.original_text)
                segment_indices.append(i)
        
        if not texts_to_translate:
            return segments
        
        try:
            # Batch translate using Google Translate
            translated_texts = []
            for text in texts_to_translate:
                translation = self.translator.translator.translate(text, src=detected_lang, dest="en")
                translated_texts.append(translation.text)
            
            # Update segments with translations
            for i, segment_idx in enumerate(segment_indices):
                segments[segment_idx].text = translated_texts[i]
                segments[segment_idx].is_translated = True
            
            logger.info(f"Successfully translated {len(translated_texts)} segments")
            
        except Exception as e:
            logger.warning(f"Batch translation failed: {e}")
            logger.info("Falling back to individual translation...")
            
            # Fallback to individual translation
            for segment in segments:
                if segment.detected_language != "en":
                    translated_text, _, was_translated = self.translator.translate_to_english(
                        segment.original_text, segment.detected_language
                    )
                    if was_translated:
                        segment.text = translated_text
                        segment.is_translated = True
        
        return segments
    
    def diarize(self, audio_path: str) -> List[SpeakerSegment]:
        """Optimized diarization using Whisper with minimal overhead"""
        try:
            if self.model is None:
                self.load_whisper_model()
            
            logger.info("Transcribing audio with Whisper...")
            
            # Simple transcription with minimal overhead
            result = self.model.transcribe(
                audio_path,
                word_timestamps=True,
                language=None,  # Auto-detect
                fp16=torch.cuda.is_available()  # Enable fp16 if GPU available
            )
            
            # Extract segments efficiently
            segments = []
            all_texts = []
            
            for i, segment in enumerate(result["segments"]):
                original_text = segment["text"].strip()
                all_texts.append(original_text)
                
                segment_obj = SpeakerSegment(
                    speaker_id=f"Speaker {i + 1}",
                    start_time=segment["start"],
                    end_time=segment["end"],
                    text=original_text,
                    original_text=original_text,
                    detected_language="",
                    is_translated=False
                )
                segments.append(segment_obj)
            
            logger.info(f"Found {len(segments)} segments")
            
            # Quick language detection
            detected_lang, confidence = self._batch_detect_language(all_texts)
            
            # Set detected language for all segments
            for segment in segments:
                segment.detected_language = detected_lang
            
            # Translate if needed
            if detected_lang != "en":
                segments = self._batch_translate_if_needed(segments, detected_lang)
            
            return segments
            
        except Exception as e:
            logger.error(f"Error in diarization: {e}")
            raise

class AudioExporter:
    """Export audio segments for each speaker"""
    
    def __init__(self):
        """Initialize audio exporter"""
        pass
    
    def export_speaker_chunks(self, audio_path: str, segments: List[SpeakerSegment], output_dir: str = "speaker_chunks"):
        """Export individual audio chunks for each spoken segment with optimized performance"""
        try:
            # Create output directory
            output_path = Path(output_dir)
            try:
                output_path.mkdir(exist_ok=True)
                logger.info(f"Output directory: {output_path.absolute()}")
            except Exception as e:
                logger.error(f"Error creating output directory: {e}")
                raise
            
            # Load audio once
            logger.info(f"Loading audio file: {audio_path}")
            try:
                audio = AudioSegment.from_file(audio_path)
                logger.info(f"Audio loaded successfully. Duration: {len(audio)/1000:.2f} seconds")
            except Exception as e:
                logger.error(f"Error loading audio file: {e}")
                raise
            
            # Sort segments by start time for chronological order
            sorted_segments = sorted(segments, key=lambda x: x.start_time)
            
            # Export individual chunks for each segment
            exported_files = []
            chunk_counter = 1
            
            for segment in sorted_segments:
                try:
                    start_ms = int(segment.start_time * 1000)
                    end_ms = int(segment.end_time * 1000)
                    
                    # Ensure valid time ranges
                    if start_ms < 0:
                        start_ms = 0
                    if end_ms > len(audio):
                        end_ms = len(audio)
                    if start_ms >= end_ms:
                        logger.warning(f"Skipping invalid segment: {start_ms}ms to {end_ms}ms")
                        continue
                    
                    # Extract the audio segment
                    logger.info(f"  Extracting segment {chunk_counter}: {segment.speaker_id} at {start_ms}ms to {end_ms}ms")
                    segment_audio = audio[start_ms:end_ms]
                    
                    # Create filename: speaker1_1, speaker1_2, speaker2_1, etc.
                    speaker_num = segment.speaker_id.replace("Speaker ", "")
                    filename = f"speaker{speaker_num}_{chunk_counter:03d}.wav"
                    output_file = output_path / filename
                    
                    # Export individual chunk
                    logger.info(f"    Exporting to: {output_file}")
                    segment_audio.export(str(output_file), format="wav")
                    
                    # Verify the file was created
                    if output_file.exists():
                        exported_files.append(str(output_file))
                        logger.info(f"    ✅ Exported: {filename} ({len(segment_audio)/1000:.2f}s)")
                    else:
                        logger.error(f"    ❌ Export failed for: {filename}")
                        
                    chunk_counter += 1
                        
                except Exception as e:
                    logger.error(f"Error processing segment {chunk_counter}: {e}")
                    chunk_counter += 1
                    continue
            
            logger.info(f"✅ Total chunks exported: {len(exported_files)}")
            return exported_files
            
        except Exception as e:
            logger.error(f"Error exporting audio chunks: {e}")
            raise

def transcribe_and_diarize(audio_path: str) -> List[SpeakerSegment]:
    """Main function to transcribe and diarize audio"""
    try:
        diarizer = SimpleDiarizer()
        diarizer.load_whisper_model("small")
        segments = diarizer.diarize(audio_path)
        return segments
    except Exception as e:
        logger.error(f"Error in transcription and diarization: {e}")
        raise

def export_speaker_chunks(audio_path: str, diarization_results: List[SpeakerSegment]) -> List[str]:
    """Export audio chunks for each speaker"""
    try:
        exporter = AudioExporter()
        exported_files = exporter.export_speaker_chunks(audio_path, diarization_results)
        return exported_files
        
    except Exception as e:
        logger.error(f"Error exporting speaker chunks: {e}")
        raise

def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python speaker_diarization_fallback.py <audio_file>")
        print("Example: python speaker_diarization_fallback.py 'audio.mp3'")
        sys.exit(1)
    
    audio_path = sys.argv[1].strip('"').strip("'")  # Remove quotes if present
    
    # Check if file exists
    if not os.path.exists(audio_path):
        print(f"Error: Audio file '{audio_path}' not found")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Files in current directory:")
        try:
            for file in os.listdir('.'):
                if file.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.ogg')):
                    print(f"  - {file}")
        except Exception as e:
            print(f"  Error listing directory: {e}")
        sys.exit(1)
    
    print(f"✅ Audio file found: {audio_path}")
    print(f"File size: {os.path.getsize(audio_path)} bytes")
    
    try:
        logger.info(f"Processing audio file: {audio_path}")
        
        # Step 1: Transcribe and diarize
        logger.info("Starting transcription and diarization...")
        segments = transcribe_and_diarize(audio_path)
        
        # Step 2: Export results to JSON
        output_file = Path(audio_path).stem + "_diarization.json"
        results = []
        
        # Sort segments by start time for chronological order
        sorted_segments = sorted(segments, key=lambda x: x.start_time)
        
        for i, segment in enumerate(sorted_segments, 1):
            speaker_num = segment.speaker_id.replace("Speaker ", "")
            chunk_id = f"speaker{speaker_num}_{i:03d}"
            
            results.append({
                "chunk_id": chunk_id,
                "chunk_number": i,
                "speaker_id": segment.speaker_id,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "duration": segment.end_time - segment.start_time,
                "text": segment.text,
                "original_text": segment.original_text,
                "detected_language": segment.detected_language,
                "is_translated": segment.is_translated,
                "audio_file": f"speaker_chunks/{chunk_id}.wav"
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_file}")
        
        # Step 3: Export individual audio chunks
        logger.info("Exporting individual audio chunks...")
        exported_files = export_speaker_chunks(audio_path, segments)
        
        logger.info(f"Exported {len(exported_files)} individual chunks")
        
        # Summary
        translated_count = sum(1 for seg in segments if seg.is_translated)
        logger.info(f"📊 Summary: {len(segments)} segments, {translated_count} translated")
        logger.info("✅ Processing completed successfully!")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 