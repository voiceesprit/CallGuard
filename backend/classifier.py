#!/usr/bin/env python3
"""
Enhanced Classifier Module
Integrates speaker analysis with scam detection for comprehensive risk assessment
"""

import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import numpy as np

# Import our modules
from asr import SpeakerSegment, get_speaker_analysis
from scam_detection import detect_scam_and_bot

logger = logging.getLogger(__name__)


@dataclass
class SpeakerProfile:
    """Profile of a speaker based on analysis"""
    speaker_id: str
    total_segments: int
    total_duration: float
    language: str
    avg_segment_length: float
    speech_patterns: Dict[str, Any]
    risk_indicators: List[str]


@dataclass
class ConversationAnalysis:
    """Comprehensive analysis of a conversation"""
    speakers: List[SpeakerProfile]
    conversation_flow: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]


class EnhancedClassifier:
    """Enhanced classifier that analyzes speaker patterns and conversation dynamics"""
    
    def __init__(self):
        """Initialize the enhanced classifier"""
        self.risk_thresholds = {
            "high_risk": 0.7,
            "medium_risk": 0.4,
            "low_risk": 0.2
        }
    
    def analyze_speakers(self, segments: List[SpeakerSegment]) -> List[SpeakerProfile]:
        """Analyze individual speakers and create profiles"""
        if not segments:
            return []
        
        # Group segments by speaker
        speaker_groups = {}
        for segment in segments:
            speaker_id = segment.speaker_id
            if speaker_id not in speaker_groups:
                speaker_groups[speaker_id] = []
            speaker_groups[speaker_id].append(segment)
        
        # Create speaker profiles
        speaker_profiles = []
        for speaker_id, speaker_segments in speaker_groups.items():
            profile = self._create_speaker_profile(speaker_id, speaker_segments)
            speaker_profiles.append(profile)
        
        return speaker_profiles
    
    def _create_speaker_profile(self, speaker_id: str, segments: List[SpeakerSegment]) -> SpeakerProfile:
        """Create a detailed profile for a single speaker"""
        # Basic statistics
        total_segments = len(segments)
        total_duration = sum(seg.end_time - seg.start_time for seg in segments)
        avg_segment_length = total_duration / total_segments if total_segments > 0 else 0
        
        # Language analysis
        languages = list(set(seg.detected_language for seg in segments))
        primary_language = languages[0] if languages else "unknown"
        
        # Speech pattern analysis
        speech_patterns = self._analyze_speech_patterns(segments)
        
        # Risk indicators
        risk_indicators = self._identify_speaker_risk_indicators(segments, speech_patterns)
        
        return SpeakerProfile(
            speaker_id=speaker_id,
            total_segments=total_segments,
            total_duration=total_duration,
            language=primary_language,
            avg_segment_length=avg_segment_length,
            speech_patterns=speech_patterns,
            risk_indicators=risk_indicators
        )
    
    def _analyze_speech_patterns(self, segments: List[SpeakerSegment]) -> Dict[str, Any]:
        """Analyze speech patterns for a speaker"""
        if not segments:
            return {}
        
        # Extract text for analysis
        all_text = " ".join([seg.text for seg in segments if seg.text.strip()])
        
        # Run scam detection on speaker's text
        scam_results = detect_scam_and_bot(all_text) if all_text.strip() else {
            "scam": "NO",
            "bot_or_human": "UNKNOWN",
            "combined_scam_score": 0.0,
            "perplexity": 0.0,
            "lang": "unknown",
            "has_filler": False
        }
        
        # Calculate speech rate (words per minute)
        total_words = len(all_text.split())
        total_duration = sum(seg.end_time - seg.start_time for seg in segments)
        words_per_minute = (total_words / total_duration * 60) if total_duration > 0 else 0
        
        # Analyze segment distribution
        segment_durations = [seg.end_time - seg.start_time for seg in segments]
        avg_duration = np.mean(segment_durations) if segment_durations else 0
        duration_variance = np.var(segment_durations) if len(segment_durations) > 1 else 0
        
        # Check for translation patterns
        translated_segments = sum(1 for seg in segments if seg.is_translated)
        translation_ratio = translated_segments / len(segments) if segments else 0
        
        return {
            "scam_score": scam_results["combined_scam_score"],
            "bot_human_score": scam_results["bot_or_human"],
            "perplexity": scam_results["perplexity"],
            "has_filler_words": scam_results["has_filler"],
            "words_per_minute": words_per_minute,
            "avg_segment_duration": avg_duration,
            "duration_variance": duration_variance,
            "translation_ratio": translation_ratio,
            "total_words": total_words,
            "total_duration": total_duration
        }
    
    def _identify_speaker_risk_indicators(self, segments: List[SpeakerSegment], patterns: Dict[str, Any]) -> List[str]:
        """Identify risk indicators for a speaker"""
        risk_indicators = []
        
        # High scam score
        if patterns.get("scam_score", 0) > self.risk_thresholds["high_risk"]:
            risk_indicators.append("High scam probability")
        
        # Bot-like behavior
        if patterns.get("bot_human_score") == "BOT-like":
            risk_indicators.append("Bot-like speech patterns")
        
        # Unusual speech rate
        wpm = patterns.get("words_per_minute", 0)
        if wpm > 200:  # Very fast speech
            risk_indicators.append("Unusually fast speech rate")
        elif wpm < 50:  # Very slow speech
            risk_indicators.append("Unusually slow speech rate")
        
        # High translation ratio
        if patterns.get("translation_ratio", 0) > 0.5:
            risk_indicators.append("High proportion of translated content")
        
        # Filler words
        if patterns.get("has_filler_words", False):
            risk_indicators.append("Filler words detected")
        
        # Inconsistent segment lengths
        if patterns.get("duration_variance", 0) > 10:  # High variance
            risk_indicators.append("Inconsistent speech patterns")
        
        return risk_indicators
    
    def analyze_conversation_flow(self, segments: List[SpeakerSegment]) -> Dict[str, Any]:
        """Analyze the flow and dynamics of the conversation"""
        if not segments:
            return {}
        
        # Sort segments by time
        sorted_segments = sorted(segments, key=lambda x: x.start_time)
        
        # Analyze speaker interactions
        speaker_turns = []
        current_speaker = None
        turn_start = 0
        
        for segment in sorted_segments:
            if current_speaker != segment.speaker_id:
                if current_speaker is not None:
                    speaker_turns.append({
                        "speaker": current_speaker,
                        "start": turn_start,
                        "end": segment.start_time,
                        "duration": segment.start_time - turn_start
                    })
                current_speaker = segment.speaker_id
                turn_start = segment.start_time
        
        # Add final turn
        if current_speaker is not None and sorted_segments:
            last_segment = sorted_segments[-1]
            speaker_turns.append({
                "speaker": current_speaker,
                "start": turn_start,
                "end": last_segment.end_time,
                "duration": last_segment.end_time - turn_start
            })
        
        # Calculate conversation metrics
        total_duration = sum(turn["duration"] for turn in speaker_turns)
        speaker_durations = {}
        for turn in speaker_turns:
            speaker = turn["speaker"]
            if speaker not in speaker_durations:
                speaker_durations[speaker] = 0
            speaker_durations[speaker] += turn["duration"]
        
        # Dominance analysis
        total_speaking_time = sum(speaker_durations.values())
        speaker_dominance = {
            speaker: duration / total_speaking_time 
            for speaker, duration in speaker_durations.items()
        } if total_speaking_time > 0 else {}
        
        # Turn-taking analysis
        turn_durations = [turn["duration"] for turn in speaker_turns]
        avg_turn_duration = np.mean(turn_durations) if turn_durations else 0
        turn_variance = np.var(turn_durations) if len(turn_durations) > 1 else 0
        
        return {
            "total_turns": len(speaker_turns),
            "total_duration": total_duration,
            "speaker_dominance": speaker_dominance,
            "avg_turn_duration": avg_turn_duration,
            "turn_variance": turn_variance,
            "speaker_turns": speaker_turns,
            "conversation_balance": self._assess_conversation_balance(speaker_dominance)
        }
    
    def _assess_conversation_balance(self, speaker_dominance: Dict[str, float]) -> str:
        """Assess the balance of the conversation"""
        if not speaker_dominance:
            return "unknown"
        
        # Check if one speaker dominates
        max_dominance = max(speaker_dominance.values())
        if max_dominance > 0.8:
            return "highly_imbalanced"
        elif max_dominance > 0.6:
            return "imbalanced"
        elif max_dominance > 0.4:
            return "moderately_balanced"
        else:
            return "well_balanced"
    
    def calculate_overall_risk(self, speaker_profiles: List[SpeakerProfile], 
                             conversation_flow: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall risk assessment"""
        if not speaker_profiles:
            return {
                "risk_level": "LOW",
                "risk_score": 0.0,
                "risk_factors": [],
                "confidence": 0.0
            }
        
        # Calculate risk scores for each speaker
        speaker_risks = []
        for profile in speaker_profiles:
            risk_score = 0.0
            risk_factors = []
            
            # Scam score contribution
            scam_score = profile.speech_patterns.get("scam_score", 0)
            risk_score += scam_score * 0.4
            
            # Bot behavior contribution
            if profile.speech_patterns.get("bot_human_score") == "BOT-like":
                risk_score += 0.3
                risk_factors.append("Bot-like behavior")
            
            # Speech pattern anomalies
            wpm = profile.speech_patterns.get("words_per_minute", 0)
            if wpm > 200 or wpm < 50:
                risk_score += 0.1
                risk_factors.append("Abnormal speech rate")
            
            # Translation ratio
            translation_ratio = profile.speech_patterns.get("translation_ratio", 0)
            if translation_ratio > 0.5:
                risk_score += 0.2
                risk_factors.append("High translation content")
            
            # Filler words
            if profile.speech_patterns.get("has_filler_words", False):
                risk_score += 0.1
                risk_factors.append("Filler words detected")
            
            speaker_risks.append({
                "speaker_id": profile.speaker_id,
                "risk_score": min(risk_score, 1.0),
                "risk_factors": risk_factors
            })
        
        # Conversation flow risk factors
        flow_risk_factors = []
        if conversation_flow.get("conversation_balance") == "highly_imbalanced":
            flow_risk_factors.append("Highly imbalanced conversation")
        
        # Calculate overall risk
        max_speaker_risk = max(risk["risk_score"] for risk in speaker_risks) if speaker_risks else 0
        avg_speaker_risk = np.mean([risk["risk_score"] for risk in speaker_risks]) if speaker_risks else 0
        
        # Combine speaker risks with conversation flow risks
        overall_risk_score = max_speaker_risk * 0.7 + avg_speaker_risk * 0.3
        
        # Add conversation flow risk
        if flow_risk_factors:
            overall_risk_score += 0.1
        
        overall_risk_score = min(overall_risk_score, 1.0)
        
        # Determine risk level
        if overall_risk_score >= self.risk_thresholds["high_risk"]:
            risk_level = "HIGH"
        elif overall_risk_score >= self.risk_thresholds["medium_risk"]:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Compile all risk factors
        all_risk_factors = []
        for risk in speaker_risks:
            all_risk_factors.extend(risk["risk_factors"])
        all_risk_factors.extend(flow_risk_factors)
        
        return {
            "risk_level": risk_level,
            "risk_score": overall_risk_score,
            "risk_factors": list(set(all_risk_factors)),  # Remove duplicates
            "confidence": self._calculate_confidence(speaker_profiles, conversation_flow),
            "speaker_risks": speaker_risks
        }
    
    def _calculate_confidence(self, speaker_profiles: List[SpeakerProfile], 
                            conversation_flow: Dict[str, Any]) -> float:
        """Calculate confidence in the risk assessment"""
        if not speaker_profiles:
            return 0.0
        
        # Factors that increase confidence
        confidence_factors = []
        
        # More speakers = higher confidence
        if len(speaker_profiles) > 1:
            confidence_factors.append(0.2)
        
        # Longer conversations = higher confidence
        total_duration = sum(profile.total_duration for profile in speaker_profiles)
        if total_duration > 60:  # More than 1 minute
            confidence_factors.append(0.2)
        elif total_duration > 30:  # More than 30 seconds
            confidence_factors.append(0.1)
        
        # More segments = higher confidence
        total_segments = sum(profile.total_segments for profile in speaker_profiles)
        if total_segments > 10:
            confidence_factors.append(0.2)
        elif total_segments > 5:
            confidence_factors.append(0.1)
        
        # Clear risk indicators = higher confidence
        total_risk_indicators = sum(len(profile.risk_indicators) for profile in speaker_profiles)
        if total_risk_indicators > 0:
            confidence_factors.append(0.3)
        
        # Base confidence
        base_confidence = 0.3
        
        return min(base_confidence + sum(confidence_factors), 1.0)
    
    def generate_recommendations(self, risk_assessment: Dict[str, Any], 
                               speaker_profiles: List[SpeakerProfile]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        risk_level = risk_assessment.get("risk_level", "LOW")
        risk_factors = risk_assessment.get("risk_factors", [])
        
        if risk_level == "HIGH":
            recommendations.append("🚨 HIGH RISK: Exercise extreme caution")
            recommendations.append("🚫 Do not provide any personal or financial information")
            recommendations.append("📞 Report to authorities immediately")
            recommendations.append("🔒 End the conversation safely")
        
        elif risk_level == "MEDIUM":
            recommendations.append("⚠️ MODERATE RISK: Proceed with caution")
            recommendations.append("🔍 Verify the caller's identity independently")
            recommendations.append("❓ Ask for official contact information")
            recommendations.append("📝 Document the conversation")
        
        else:
            recommendations.append("✅ LOW RISK: No immediate concerns detected")
            recommendations.append("👂 Continue normal conversation")
        
        # Specific recommendations based on risk factors
        for factor in risk_factors:
            if "scam" in factor.lower():
                recommendations.append("💰 Be wary of any financial requests")
            elif "bot" in factor.lower():
                recommendations.append("🤖 Verify you're speaking with a human")
            elif "translation" in factor.lower():
                recommendations.append("🌍 Be aware of potential language barriers")
            elif "filler" in factor.lower():
                recommendations.append("💬 Speaker may be deceptive or nervous")
        
        return recommendations
    
    def analyze_conversation(self, segments: List[SpeakerSegment]) -> ConversationAnalysis:
        """Perform comprehensive conversation analysis"""
        # Analyze individual speakers
        speaker_profiles = self.analyze_speakers(segments)
        
        # Analyze conversation flow
        conversation_flow = self.analyze_conversation_flow(segments)
        
        # Calculate overall risk
        risk_assessment = self.calculate_overall_risk(speaker_profiles, conversation_flow)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(risk_assessment, speaker_profiles)
        
        return ConversationAnalysis(
            speakers=speaker_profiles,
            conversation_flow=conversation_flow,
            risk_assessment=risk_assessment,
            recommendations=recommendations
        )


# Global classifier instance
classifier = EnhancedClassifier()


def analyze_conversation(segments: List[SpeakerSegment]) -> Dict[str, Any]:
    """Main function to analyze conversation and return comprehensive results"""
    try:
        analysis = classifier.analyze_conversation(segments)
        
        return {
            "speakers": [
                {
                    "speaker_id": profile.speaker_id,
                    "total_segments": profile.total_segments,
                    "total_duration": profile.total_duration,
                    "language": profile.language,
                    "avg_segment_length": profile.avg_segment_length,
                    "speech_patterns": profile.speech_patterns,
                    "risk_indicators": profile.risk_indicators
                }
                for profile in analysis.speakers
            ],
            "conversation_flow": analysis.conversation_flow,
            "risk_assessment": analysis.risk_assessment,
            "recommendations": analysis.recommendations
        }
    except Exception as e:
        logger.error(f"Error in conversation analysis: {e}")
        return {
            "error": "Analysis failed",
            "details": str(e)
        }
