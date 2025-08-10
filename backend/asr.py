#!/usr/bin/env python3
"""
ASR (Automatic Speech Recognition) Module with Speaker Diarization
Integrated with the scam detection backend
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
import io

# Suppress warnings
warnings.filterwarnings("ignore")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SpeakerSegment:
    """Represents a segment of speech from a speaker"""
    speaker_id: str
    start_time: float
    end_time: float
    text: str
    original_text: str = ""
    detected_language: str = ""
    is_translated: bool = False


class AudioTranslator:
    """Handles language detection and translation of audio segments"""
    
    def __init__(self):
        """Initialize the translator"""
        self.translator = Translator()
        self._language_cache = {}
        
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
            
            # Method 1: Use langdetect library
            try:
                DetectorFactory.seed = 0
                detected_lang = detect(clean_text)
                confidence = self._get_langdetect_confidence(clean_text, detected_lang)
                
                if confidence > 0.7:
                    self._language_cache[text_hash] = detected_lang
                    return detected_lang
            except Exception as e:
                logger.debug(f"langdetect failed: {e}")
            
            # Method 2: Enhanced keyword-based detection
            keyword_lang = self._keyword_based_detection(clean_text)
            if keyword_lang != "unknown":
                self._language_cache[text_hash] = keyword_lang
                return keyword_lang
            
            # Method 3: Character pattern analysis
            pattern_lang = self._pattern_based_detection(clean_text)
            if pattern_lang != "unknown":
                self._language_cache[text_hash] = pattern_lang
                return pattern_lang
            
            # Method 4: Use Google Translate's language detection
            try:
                translation = self.translator.translate(clean_text, dest="en")
                detected_lang = translation.src
                if detected_lang != "en":
                    self._language_cache[text_hash] = detected_lang
                    return detected_lang
            except Exception as e:
                logger.debug(f"Google Translate detection failed: {e}")
            
            # Default to English
            self._language_cache[text_hash] = "en"
            return "en"
                
        except Exception as e:
            logger.warning(f"Error in language detection: {e}")
            self._language_cache[text_hash] = "unknown"
            return "unknown"
    
    def _clean_text_for_detection(self, text: str) -> str:
        """Clean text for better language detection"""
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
            
            for detection in detections:
                if detection.lang == detected_lang:
                    return detection.prob
            
            return 0.0
        except ImportError:
            logger.warning("langdetect.detect_langs not available, using default confidence")
            return 0.5
        except Exception as e:
            logger.debug(f"Error calculating langdetect confidence: {e}")
            return 0.5

    def _keyword_based_detection(self, text: str) -> str:
        """Enhanced keyword-based language detection"""
        text_lower = text.lower()
        
        # Spanish keywords
        spanish_words = ['hola', 'gracias', 'por favor', 'buenos días', 'buenas tardes', 
                        'adiós', 'sí', 'no', 'pero', 'y', 'o', 'que', 'como', 'donde', 
                        'cuando', 'porque', 'muy', 'mucho', 'poco', 'bien', 'mal']
        spanish_count = sum(1 for word in spanish_words if word in text_lower)
        
        # French keywords
        french_words = ['bonjour', 'merci', 's\'il vous plaît', 'au revoir', 'oui', 'non',
                       'mais', 'et', 'ou', 'que', 'comment', 'où', 'quand', 'pourquoi',
                       'très', 'beaucoup', 'peu', 'bien', 'mal']
        french_count = sum(1 for word in french_words if word in text_lower)
        
        # German keywords
        german_words = ['hallo', 'danke', 'bitte', 'auf wiedersehen', 'ja', 'nein',
                       'aber', 'und', 'oder', 'was', 'wie', 'wo', 'wann', 'warum',
                       'sehr', 'viel', 'wenig', 'gut', 'schlecht']
        german_count = sum(1 for word in german_words if word in text_lower)
        
        # Italian keywords
        italian_words = ['ciao', 'grazie', 'per favore', 'arrivederci', 'sì', 'no',
                        'ma', 'e', 'o', 'che', 'come', 'dove', 'quando', 'perché',
                        'molto', 'poco', 'bene', 'male']
        italian_count = sum(1 for word in italian_words if word in text_lower)
        
        # Portuguese keywords
        portuguese_words = ['olá', 'obrigado', 'por favor', 'adeus', 'sim', 'não',
                           'mas', 'e', 'ou', 'que', 'como', 'onde', 'quando', 'porque',
                           'muito', 'pouco', 'bem', 'mal']
        portuguese_count = sum(1 for word in portuguese_words if word in text_lower)
        
        # Count total words for percentage calculation
        total_words = len(text.split())
        if total_words == 0:
            return "unknown"
        
        # Calculate percentages
        spanish_pct = spanish_count / total_words
        french_pct = french_count / total_words
        german_pct = german_count / total_words
        italian_pct = italian_count / total_words
        portuguese_pct = portuguese_count / total_words
        
        # Return language with highest percentage (minimum 20% threshold)
        max_pct = max(spanish_pct, french_pct, german_pct, italian_pct, portuguese_pct)
        
        if max_pct >= 0.2:
            if max_pct == spanish_pct:
                return "es"
            elif max_pct == french_pct:
                return "fr"
            elif max_pct == german_pct:
                return "de"
            elif max_pct == italian_pct:
                return "it"
            elif max_pct == portuguese_pct:
                return "pt"
        
        return "unknown"

    def _pattern_based_detection(self, text: str) -> str:
        """Pattern-based language detection using character analysis"""
        # Character frequency analysis
        char_freq = {}
        for char in text.lower():
            if char.isalpha():
                char_freq[char] = char_freq.get(char, 0) + 1
        
        total_chars = sum(char_freq.values())
        if total_chars == 0:
            return "unknown"
        
        # Spanish patterns
        spanish_chars = ['ñ', 'á', 'é', 'í', 'ó', 'ú', 'ü']
        spanish_score = sum(char_freq.get(char, 0) for char in spanish_chars) / total_chars
        
        # French patterns
        french_chars = ['à', 'â', 'ä', 'ç', 'é', 'è', 'ê', 'ë', 'î', 'ï', 'ô', 'ö', 'ù', 'û', 'ü', 'ÿ']
        french_score = sum(char_freq.get(char, 0) for char in french_chars) / total_chars
        
        # German patterns
        german_chars = ['ä', 'ö', 'ü', 'ß']
        german_score = sum(char_freq.get(char, 0) for char in german_chars) / total_chars
        
        # Italian patterns
        italian_chars = ['à', 'è', 'é', 'ì', 'í', 'î', 'ò', 'ó', 'ù']
        italian_score = sum(char_freq.get(char, 0) for char in italian_chars) / total_chars
        
        # Portuguese patterns
        portuguese_chars = ['à', 'á', 'â', 'ã', 'ç', 'é', 'ê', 'í', 'ó', 'ô', 'õ', 'ú']
        portuguese_score = sum(char_freq.get(char, 0) for char in portuguese_chars) / total_chars
        
        # Return language with highest score (minimum 5% threshold)
        max_score = max(spanish_score, french_score, german_score, italian_score, portuguese_score)
        
        if max_score >= 0.05:
            if max_score == spanish_score:
                return "es"
            elif max_score == french_score:
                return "fr"
            elif max_score == german_score:
                return "de"
            elif max_score == italian_score:
                return "it"
            elif max_score == portuguese_score:
                return "pt"
        
        return "unknown"

    def get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name from code"""
        language_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "hi": "Hindi",
            "nl": "Dutch",
            "sv": "Swedish",
            "no": "Norwegian",
            "da": "Danish",
            "fi": "Finnish",
            "pl": "Polish",
            "tr": "Turkish",
            "he": "Hebrew",
            "th": "Thai",
            "vi": "Vietnamese",
            "id": "Indonesian",
            "ms": "Malay",
            "fa": "Persian",
            "ur": "Urdu",
            "bn": "Bengali",
            "ta": "Tamil",
            "te": "Telugu",
            "ml": "Malayalam",
            "kn": "Kannada",
            "gu": "Gujarati",
            "pa": "Punjabi",
            "mr": "Marathi",
            "ne": "Nepali",
            "si": "Sinhala",
            "my": "Burmese",
            "km": "Khmer",
            "lo": "Lao",
            "ka": "Georgian",
            "am": "Amharic",
            "sw": "Swahili",
            "zu": "Zulu",
            "af": "Afrikaans",
            "hr": "Croatian",
            "cs": "Czech",
            "sk": "Slovak",
            "sl": "Slovenian",
            "hu": "Hungarian",
            "ro": "Romanian",
            "bg": "Bulgarian",
            "mk": "Macedonian",
            "sr": "Serbian",
            "bs": "Bosnian",
            "me": "Montenegrin",
            "sq": "Albanian",
            "et": "Estonian",
            "lv": "Latvian",
            "lt": "Lithuanian",
            "uk": "Ukrainian",
            "be": "Belarusian",
            "kk": "Kazakh",
            "ky": "Kyrgyz",
            "uz": "Uzbek",
            "tg": "Tajik",
            "mn": "Mongolian",
            "ka": "Georgian",
            "hy": "Armenian",
            "az": "Azerbaijani",
            "unknown": "Unknown"
        }
        return language_names.get(lang_code, f"Unknown ({lang_code})")

    def translate_to_english(self, text: str, source_lang: str = None) -> Tuple[str, str, bool]:
        """Translate text to English"""
        try:
            if not text.strip():
                return text, "en", False
            
            # Detect language if not provided
            if source_lang is None:
                source_lang = self.detect_language(text)
            
            # Don't translate if already English
            if source_lang == "en":
                return text, "en", False
            
            # Translate to English
            translation = self.translator.translate(text, src=source_lang, dest="en")
            translated_text = translation.text
            
            return translated_text, source_lang, True
            
        except Exception as e:
            logger.warning(f"Translation failed: {e}")
            return text, source_lang or "unknown", False


class ASRProcessor:
    """Main ASR processor with speaker diarization"""
    
    def __init__(self):
        """Initialize the ASR processor"""
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
        
        # Batch translate
        for i, original_text in enumerate(texts_to_translate):
            translated_text, source_lang, was_translated = self.translator.translate_to_english(
                original_text, detected_lang
            )
            if was_translated:
                segment_index = segment_indices[i]
                segments[segment_index].text = translated_text
                segments[segment_index].is_translated = True
        
        return segments
    
    def _perform_speaker_diarization(self, segments: List[SpeakerSegment], audio_array: np.ndarray) -> List[SpeakerSegment]:
        """Perform speaker diarization to identify different speakers"""
        try:
            if len(segments) <= 1:
                # Only one segment, no diarization needed
                if segments:
                    segments[0].speaker_id = "Speaker 1"
                return segments
            
            logger.info("Performing speaker diarization...")
            
            # Simple diarization based on timing and content patterns
            speakers = self._simple_diarization(segments)
            
            # Update speaker IDs
            for segment in segments:
                segment.speaker_id = speakers.get(segment, "Speaker 1")
            
            # Count unique speakers
            unique_speakers = len(set(speakers.values()))
            logger.info(f"Identified {unique_speakers} speakers")
            
            return segments
            
        except Exception as e:
            logger.error(f"Error in speaker diarization: {e}")
            # Fallback: assign all to Speaker 1
            for segment in segments:
                segment.speaker_id = "Speaker 1"
            return segments
    
    def _simple_diarization(self, segments: List[SpeakerSegment]) -> List[SpeakerSegment]:
        """Simple speaker diarization based on timing and content patterns"""
        if not segments:
            return segments
        
        # Start with first speaker (empty label)
        current_speaker = ""
        segments[0].speaker_id = current_speaker
        speaker_count = 1
        
        # More aggressive speaker change detection
        for i in range(1, len(segments)):
            prev_segment = segments[i-1]
            curr_segment = segments[i]
            
            # Calculate time gap between segments
            time_gap = curr_segment.start_time - prev_segment.end_time
            
            # Simple rule: if gap > 1 second, likely different speaker
            # Also alternate speakers every few segments to ensure variety
            if time_gap > 1.0 or i % 3 == 0:  # Change speaker every 3 segments or on gaps
                speaker_count += 1
                current_speaker = ""  # Empty label for separation
            else:
                current_speaker = ""  # Same speaker, keep empty
            
            curr_segment.speaker_id = current_speaker
        
        return segments
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity between two segments"""
        if not text1.strip() or not text2.strip():
            return 0.0
        
        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _is_likely_same_speaker(self, time_gap: float, text_similarity: float, 
                               prev_segment: SpeakerSegment, curr_segment: SpeakerSegment) -> bool:
        """Determine if two segments are likely from the same speaker"""
        
        # Factors that suggest same speaker:
        # 1. Short time gap (less than 1.5 seconds)
        # 2. High text similarity
        # 3. Similar segment lengths
        # 4. Continuation patterns (e.g., "and", "but", "so")
        
        # Time gap factor - more sensitive to gaps
        time_factor = 1.0 if time_gap < 1.5 else 0.3 if time_gap < 3.0 else 0.1
        
        # Text similarity factor
        similarity_factor = text_similarity
        
        # Length similarity factor
        len1, len2 = len(prev_segment.text), len(curr_segment.text)
        length_factor = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 0.0
        
        # Continuation pattern factor
        continuation_words = ["and", "but", "so", "then", "also", "however", "therefore", "thus", "well", "um", "uh"]
        continuation_factor = 0.0
        if curr_segment.text.lower().startswith(tuple(continuation_words)):
            continuation_factor = 0.4
        
        # Combined score - lower threshold for speaker change
        score = (time_factor * 0.4 + similarity_factor * 0.3 + length_factor * 0.2 + continuation_factor * 0.1)
        
        # More aggressive speaker change detection
        return score > 0.6
    
    def _perform_simple_diarization(self, segments: List[SpeakerSegment]) -> List[SpeakerSegment]:
        """Simple diarization for file processing (without audio array)"""
        try:
            if len(segments) <= 1:
                # Only one segment, no diarization needed
                if segments:
                    segments[0].speaker_id = "Speaker 1"
                return segments
            
            logger.info("Performing simple speaker diarization...")
            
            # Simple diarization based on timing and content patterns
            speakers = self._simple_diarization(segments)
            
            # Update speaker IDs
            for segment in segments:
                segment.speaker_id = speakers.get(segment, "Speaker 1")
            
            # Count unique speakers
            unique_speakers = len(set(speakers.values()))
            logger.info(f"Identified {unique_speakers} speakers")
            
            return segments
            
        except Exception as e:
            logger.error(f"Error in simple diarization: {e}")
            # Fallback: assign all to Speaker 1
            for segment in segments:
                segment.speaker_id = "Speaker 1"
            return segments
    
    def process_audio_bytes(self, audio_bytes: bytes) -> List[SpeakerSegment]:
        """Process audio bytes and return speaker segments"""
        try:
            if self.model is None:
                self.load_whisper_model()
            
            logger.info("Processing audio bytes with Whisper...")
            
            # Convert bytes to audio segment and then to numpy array
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # Convert to mono and normalize
            audio_segment = audio_segment.set_channels(1)
            audio_segment = audio_segment.set_frame_rate(16000)
            
            # Convert to numpy array
            audio_array = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
            audio_array = audio_array / (2**15)  # Normalize to [-1, 1]
            
            # Simple transcription with minimal overhead
            result = self.model.transcribe(
                audio_array,
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
                    speaker_id=f"Speaker {i + 1}",  # Will be updated by diarization
                    start_time=segment["start"],
                    end_time=segment["end"],
                    text=original_text,
                    original_text=original_text,
                    detected_language="",
                    is_translated=False
                )
                segments.append(segment_obj)
            
            logger.info(f"Found {len(segments)} segments")
            
            # Perform speaker diarization
            segments = self._perform_speaker_diarization(segments, audio_array)
            
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
            logger.error(f"Error in audio processing: {e}")
            raise
    
    def process_audio_file(self, audio_path: str) -> List[SpeakerSegment]:
        """Process audio file and return speaker segments"""
        try:
            if self.model is None:
                self.load_whisper_model()
            
            logger.info("Processing audio file with Whisper...")
            
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
            
            # Perform speaker diarization (simple approach for file processing)
            segments = self._perform_simple_diarization(segments)
            
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
            logger.error(f"Error in audio processing: {e}")
            raise


# Global ASR processor instance
asr_processor = ASRProcessor()


def process_audio(audio_bytes: bytes = None, audio_path: str = None) -> List[SpeakerSegment]:
    """Main function to process audio and return speaker segments"""
    if audio_bytes:
        return asr_processor.process_audio_bytes(audio_bytes)
    elif audio_path:
        return asr_processor.process_audio_file(audio_path)
    else:
        raise ValueError("Either audio_bytes or audio_path must be provided")


def get_speaker_text(segments: List[SpeakerSegment]) -> str:
    """Extract all text from speaker segments"""
    return " ".join([segment.text for segment in segments if segment.text.strip()])


def get_formatted_transcript(segments: List[SpeakerSegment]) -> str:
    """Format transcript with timestamps (no speaker labels)"""
    if not segments:
        return "No transcript available"
    
    formatted_lines = []
    for segment in segments:
        if segment.text.strip():
            # Format: (0:00 - 0:05): Hello, how are you?
            start_time = format_time(segment.start_time)
            end_time = format_time(segment.end_time)
            formatted_lines.append(f"({start_time} - {end_time}): {segment.text}")
    
    return "\n".join(formatted_lines)


def format_time(seconds: float) -> str:
    """Format seconds to MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def get_speaker_analysis(segments: List[SpeakerSegment]) -> Dict:
    """Get comprehensive analysis of speaker segments"""
    if not segments:
        return {
            "total_segments": 0,
            "total_duration": 0,
            "languages": [],
            "translated_segments": 0
        }
    
    # Calculate statistics
    total_duration = sum(segment.end_time - segment.start_time for segment in segments)
    languages = list(set(segment.detected_language for segment in segments))
    translated_count = sum(1 for segment in segments if segment.is_translated)
    
    # Get all text
    all_text = get_speaker_text(segments)
    formatted_transcript = get_formatted_transcript(segments)
    
    return {
        "total_segments": len(segments),
        "total_duration": total_duration,
        "languages": languages,
        "translated_segments": translated_count,
        "full_text": all_text,
        "formatted_transcript": formatted_transcript,
        "segments": [
            {
                "speaker_id": segment.speaker_id,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "text": segment.text,
                "original_text": segment.original_text,
                "detected_language": segment.detected_language,
                "is_translated": segment.is_translated
            }
            for segment in segments
        ]
    }
