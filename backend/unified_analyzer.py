#!/usr/bin/env python3
"""
Unified Audio Analysis Platform for Real-time Voice Call Scam Detection
Combines ASR, anti-spoof, scam detection, and classification into a single pipeline
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np

# Import our analysis modules
from asr import process_audio, get_speaker_analysis, SpeakerSegment
from anti_spoof import detect_audio_spoofing, get_spoof_recommendations
from scam_detection import detect_scam_and_bot
from classifier import analyze_conversation

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Complete analysis result for a voice call"""
    # Audio metadata
    audio_duration: float
    file_size_bytes: int
    processing_time: float
    
    # Speech recognition results
    transcript: str
    segments_count: int
    languages_detected: List[str]
    translated_segments: int
    
    # Anti-spoof results
    is_authentic: bool
    spoof_probability: float
    spoof_confidence: float
    
    # Scam detection results
    is_scam: bool
    scam_score: float
    bot_or_human: str
    perplexity: float
    has_filler_words: bool
    
    # Risk assessment
    overall_risk_level: str
    risk_score: float
    risk_factors: List[str]
    confidence: float
    
    # Recommendations
    recommendations: List[str]
    
    # Detailed analysis
    speaker_profiles: List[Dict[str, Any]]
    conversation_flow: Dict[str, Any]
    analysis_timestamp: str


class UnifiedAnalyzer:
    """Unified analyzer for real-time voice call scam detection"""
    
    def __init__(self):
        """Initialize the unified analyzer"""
        self.analysis_count = 0
        self.total_processing_time = 0.0
        
    def analyze_voice_call(self, audio_bytes: bytes, call_id: str = None) -> AnalysisResult:
        """
        Complete analysis of a voice call for scam detection
        Returns comprehensive results with risk assessment
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting unified analysis for call {call_id or 'unknown'}")
            
            # Step 1: Anti-spoof detection (fastest, do first)
            logger.info("Step 1/4: Anti-spoof detection...")
            spoof_start = time.time()
            spoof_results = detect_audio_spoofing(audio_bytes)
            spoof_time = time.time() - spoof_start
            
            # Step 2: Speech recognition and diarization
            logger.info("Step 2/4: Speech recognition and diarization...")
            asr_start = time.time()
            speaker_segments = process_audio(audio_bytes=audio_bytes)
            asr_time = time.time() - asr_start
            
            # Step 3: Extract text and run scam detection
            logger.info("Step 3/4: Scam detection...")
            scam_start = time.time()
            full_text = " ".join([seg.text for seg in speaker_segments if seg.text.strip()])
            scam_results = detect_scam_and_bot(full_text) if full_text.strip() else {
                "scam": "NO",
                "bot_or_human": "UNKNOWN",
                "combined_scam_score": 0.0,
                "perplexity": 0.0,
                "lang": "unknown",
                "has_filler": False
            }
            scam_time = time.time() - scam_start
            
            # Step 4: Enhanced classification and conversation analysis
            logger.info("Step 4/4: Conversation analysis...")
            classifier_start = time.time()
            conversation_analysis = analyze_conversation(speaker_segments)
            classifier_time = time.time() - classifier_start
            
            # Calculate overall processing time
            total_time = time.time() - start_time
            
            # Compile comprehensive results
            result = self._compile_results(
                audio_bytes=audio_bytes,
                speaker_segments=speaker_segments,
                spoof_results=spoof_results,
                scam_results=scam_results,
                conversation_analysis=conversation_analysis,
                processing_times={
                    "total": total_time,
                    "spoof": spoof_time,
                    "asr": asr_time,
                    "scam": scam_time,
                    "classifier": classifier_time
                },
                call_id=call_id
            )
            
            # Update statistics
            self.analysis_count += 1
            self.total_processing_time += total_time
            
            logger.info(f"Analysis completed in {total_time:.2f}s")
            logger.info(f"Risk Level: {result.overall_risk_level}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in unified analysis: {e}")
            # Return error result
            return self._create_error_result(audio_bytes, str(e), call_id)
    
    def _compile_results(self, audio_bytes: bytes, speaker_segments: List[SpeakerSegment],
                        spoof_results: Dict[str, Any], scam_results: Dict[str, Any],
                        conversation_analysis: Dict[str, Any], processing_times: Dict[str, float],
                        call_id: str = None) -> AnalysisResult:
        """Compile all analysis results into a unified result"""
        
        # Get speaker analysis
        speaker_analysis = get_speaker_analysis(speaker_segments)
        
        # Calculate risk score
        risk_score = self._calculate_unified_risk_score(
            spoof_results, scam_results, conversation_analysis
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        # Compile risk factors
        risk_factors = self._compile_risk_factors(
            spoof_results, scam_results, conversation_analysis
        )
        
        # Generate recommendations
        recommendations = self._generate_unified_recommendations(
            spoof_results, scam_results, conversation_analysis, risk_level
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            spoof_results, scam_results, conversation_analysis
        )
        
        return AnalysisResult(
            # Audio metadata
            audio_duration=speaker_analysis.get("total_duration", 0),
            file_size_bytes=len(audio_bytes),
            processing_time=processing_times["total"],
            
            # Speech recognition results
            transcript=speaker_analysis.get("formatted_transcript", ""),
            segments_count=speaker_analysis.get("total_segments", 0),
            languages_detected=speaker_analysis.get("languages", []),
            translated_segments=speaker_analysis.get("translated_segments", 0),
            
            # Anti-spoof results
            is_authentic=spoof_results.get("is_authentic", False),
            spoof_probability=spoof_results.get("spoof_probability", 1.0),
            spoof_confidence=spoof_results.get("confidence", 0.0),
            
            # Scam detection results
            is_scam=scam_results.get("scam") == "YES",
            scam_score=scam_results.get("combined_scam_score", 0.0),
            bot_or_human=scam_results.get("bot_or_human", "UNKNOWN"),
            perplexity=scam_results.get("perplexity", 0.0),
            has_filler_words=scam_results.get("has_filler", False),
            
            # Risk assessment
            overall_risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
            confidence=confidence,
            
            # Recommendations
            recommendations=recommendations,
            
            # Detailed analysis
            speaker_profiles=conversation_analysis.get("speakers", []),
            conversation_flow=conversation_analysis.get("conversation_flow", {}),
            analysis_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def _calculate_unified_risk_score(self, spoof_results: Dict[str, Any],
                                    scam_results: Dict[str, Any],
                                    conversation_analysis: Dict[str, Any]) -> float:
        """Calculate unified risk score from all analysis components"""
        
        # Anti-spoof risk (40% weight)
        spoof_risk = spoof_results.get("spoof_probability", 1.0) * 0.4
        
        # Scam risk (35% weight)
        scam_risk = scam_results.get("combined_scam_score", 0.0) * 0.35
        
        # Bot behavior risk (15% weight)
        bot_risk = 0.0
        if scam_results.get("bot_or_human") == "BOT-like":
            bot_risk = 0.15
        
        # Conversation flow risk (10% weight)
        flow_risk = 0.0
        risk_assessment = conversation_analysis.get("risk_assessment", {})
        if risk_assessment.get("risk_level") == "HIGH":
            flow_risk = 0.1
        elif risk_assessment.get("risk_level") == "MEDIUM":
            flow_risk = 0.05
        
        # Calculate total risk
        total_risk = spoof_risk + scam_risk + bot_risk + flow_risk
        
        return min(total_risk, 1.0)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on unified risk score"""
        if risk_score >= 0.7:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _compile_risk_factors(self, spoof_results: Dict[str, Any],
                            scam_results: Dict[str, Any],
                            conversation_analysis: Dict[str, Any]) -> List[str]:
        """Compile all risk factors from different analyses"""
        risk_factors = []
        
        # Anti-spoof risk factors
        if spoof_results.get("spoof_probability", 0) > 0.5:
            risk_factors.append("High spoof probability detected")
        
        # Scam risk factors
        if scam_results.get("combined_scam_score", 0) > 0.6:
            risk_factors.append("High scam probability")
        
        if scam_results.get("bot_or_human") == "BOT-like":
            risk_factors.append("Bot-like speech patterns")
        
        if scam_results.get("has_filler", False):
            risk_factors.append("Filler words detected")
        
        # Conversation risk factors
        risk_assessment = conversation_analysis.get("risk_assessment", {})
        risk_factors.extend(risk_assessment.get("risk_factors", []))
        
        return list(set(risk_factors))  # Remove duplicates
    
    def _generate_unified_recommendations(self, spoof_results: Dict[str, Any],
                                        scam_results: Dict[str, Any],
                                        conversation_analysis: Dict[str, Any],
                                        risk_level: str) -> List[str]:
        """Generate unified recommendations based on all analyses"""
        recommendations = []
        
        # Base recommendations by risk level
        if risk_level == "HIGH":
            recommendations.extend([
                "🚨 HIGH RISK: Exercise extreme caution",
                "🚫 Do not provide personal or financial information",
                "📞 Report to authorities immediately",
                "🔒 End the conversation safely"
            ])
        elif risk_level == "MEDIUM":
            recommendations.extend([
                "⚠️ MODERATE RISK: Proceed with caution",
                "🔍 Verify the caller's identity independently",
                "❓ Ask for official contact information",
                "📝 Document the conversation"
            ])
        else:
            recommendations.extend([
                "✅ LOW RISK: No immediate concerns detected",
                "👂 Continue normal conversation",
                "🔍 Monitor for changes in behavior"
            ])
        
        # Add specific recommendations from conversation analysis
        conv_recommendations = conversation_analysis.get("recommendations", [])
        recommendations.extend(conv_recommendations)
        
        # Add spoof-specific recommendations
        if not spoof_results.get("is_authentic", True):
            recommendations.extend([
                "🎵 Audio authenticity concerns detected",
                "🔍 Verify caller through alternative means"
            ])
        
        return list(set(recommendations))  # Remove duplicates
    
    def _calculate_confidence(self, spoof_results: Dict[str, Any],
                            scam_results: Dict[str, Any],
                            conversation_analysis: Dict[str, Any]) -> float:
        """Calculate overall confidence in the analysis"""
        
        # Base confidence from each component
        spoof_confidence = spoof_results.get("confidence", 0.0) * 0.3
        conversation_confidence = conversation_analysis.get("risk_assessment", {}).get("confidence", 0.0) * 0.4
        
        # Scam detection confidence (based on text length and quality)
        scam_confidence = 0.0
        if scam_results.get("perplexity", 0) > 0:
            scam_confidence = min(0.3, 0.3 * (scam_results.get("perplexity", 0) / 100))
        
        total_confidence = spoof_confidence + conversation_confidence + scam_confidence
        
        return min(total_confidence, 1.0)
    
    def _create_error_result(self, audio_bytes: bytes, error_message: str, call_id: str = None) -> AnalysisResult:
        """Create error result when analysis fails"""
        return AnalysisResult(
            # Audio metadata
            audio_duration=0.0,
            file_size_bytes=len(audio_bytes),
            processing_time=0.0,
            
            # Speech recognition results
            transcript="",
            segments_count=0,
            languages_detected=[],
            translated_segments=0,
            
            # Anti-spoof results
            is_authentic=False,
            spoof_probability=1.0,
            spoof_confidence=0.0,
            
            # Scam detection results
            is_scam=False,
            scam_score=0.0,
            bot_or_human="UNKNOWN",
            perplexity=0.0,
            has_filler_words=False,
            
            # Risk assessment
            overall_risk_level="HIGH",
            risk_score=1.0,
            risk_factors=[f"Analysis failed: {error_message}"],
            confidence=0.0,
            
            # Recommendations
            recommendations=[
                "🚨 Analysis failed - exercise extreme caution",
                "🔍 Verify caller identity through other means",
                "📞 Contact support if this persists"
            ],
            
            # Detailed analysis
            speaker_profiles=[],
            conversation_flow={},
            analysis_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        avg_time = self.total_processing_time / self.analysis_count if self.analysis_count > 0 else 0
        
        return {
            "total_analyses": self.analysis_count,
            "total_processing_time": self.total_processing_time,
            "average_processing_time": avg_time,
            "platform_status": "operational"
        }


# Global unified analyzer instance
unified_analyzer = UnifiedAnalyzer()


def analyze_voice_call(audio_bytes: bytes, call_id: str = None) -> Dict[str, Any]:
    """Main function to analyze a voice call for scam detection"""
    try:
        result = unified_analyzer.analyze_voice_call(audio_bytes, call_id)
        return asdict(result)
    except Exception as e:
        logger.error(f"Error in voice call analysis: {e}")
        return {
            "error": "Analysis failed",
            "details": str(e),
            "overall_risk_level": "HIGH",
            "recommendations": [
                "🚨 Analysis failed - exercise extreme caution",
                "🔍 Verify caller identity through other means"
            ]
        }


def get_platform_statistics() -> Dict[str, Any]:
    """Get platform statistics"""
    return unified_analyzer.get_statistics() 