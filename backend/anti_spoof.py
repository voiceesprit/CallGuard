#!/usr/bin/env python3
"""
Anti-Spoof Detection Module
Integrates with the existing AASIST workflow for audio authenticity verification
"""

import logging
import numpy as np
import torch
import soundfile as sf
import librosa
import io
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

# Import the existing workflow
from workflow import detect_spoof_from_bytes

logger = logging.getLogger(__name__)


@dataclass
class SpoofAnalysis:
    """Comprehensive spoof analysis results"""
    is_authentic: bool
    spoof_probability: float
    confidence: float
    risk_level: str
    detection_method: str
    analysis_details: Dict[str, Any]


class AntiSpoofDetector:
    """Enhanced anti-spoof detector with multiple analysis methods"""
    
    def __init__(self):
        """Initialize the anti-spoof detector"""
        self.risk_thresholds = {
            "high_risk": 0.7,
            "medium_risk": 0.4,
            "low_risk": 0.2
        }
    
    def analyze_audio_authenticity(self, audio_bytes: bytes) -> SpoofAnalysis:
        """
        Comprehensive audio authenticity analysis
        """
        try:
            # Primary analysis using AASIST
            spoof_prob, spoof_label = detect_spoof_from_bytes(audio_bytes)
            
            # Additional analysis methods
            audio_analysis = self._analyze_audio_characteristics(audio_bytes)
            
            # Determine risk level
            risk_level = self._determine_risk_level(spoof_prob)
            
            # Calculate confidence
            confidence = self._calculate_confidence(spoof_prob, audio_analysis)
            
            # Compile analysis details
            analysis_details = {
                "aasist_results": {
                    "spoof_probability": spoof_prob,
                    "spoof_label": spoof_label
                },
                "audio_characteristics": audio_analysis,
                "risk_factors": self._identify_risk_factors(spoof_prob, audio_analysis)
            }
            
            return SpoofAnalysis(
                is_authentic=spoof_label == "BONAFIDE",
                spoof_probability=spoof_prob,
                confidence=confidence,
                risk_level=risk_level,
                detection_method="AASIST + Audio Analysis",
                analysis_details=analysis_details
            )
            
        except Exception as e:
            logger.error(f"Error in audio authenticity analysis: {e}")
            return SpoofAnalysis(
                is_authentic=False,
                spoof_probability=1.0,
                confidence=0.0,
                risk_level="HIGH",
                detection_method="Error",
                analysis_details={"error": str(e)}
            )
    
    def _analyze_audio_characteristics(self, audio_bytes: bytes) -> Dict[str, Any]:
        """Analyze audio characteristics for additional spoof detection"""
        try:
            # Convert bytes to audio data
            audio_buffer = io.BytesIO(audio_bytes)
            data, sr = sf.read(audio_buffer)
            data = np.asarray(data)
            
            # Convert to mono if stereo
            if data.ndim > 1:
                data = data.mean(axis=1)
            
            # Ensure float32
            data = data.astype(np.float32)
            
            # Resample to 16kHz if needed
            if sr != 16000:
                data = librosa.resample(data, orig_sr=sr, target_sr=16000)
            
            # Audio characteristic analysis
            characteristics = {}
            
            # 1. Signal-to-Noise Ratio (SNR)
            characteristics["snr"] = self._calculate_snr(data)
            
            # 2. Spectral characteristics
            characteristics["spectral_features"] = self._analyze_spectral_features(data)
            
            # 3. Temporal characteristics
            characteristics["temporal_features"] = self._analyze_temporal_features(data)
            
            # 4. Energy distribution
            characteristics["energy_distribution"] = self._analyze_energy_distribution(data)
            
            # 5. Frequency analysis
            characteristics["frequency_analysis"] = self._analyze_frequency_content(data)
            
            return characteristics
            
        except Exception as e:
            logger.warning(f"Error in audio characteristic analysis: {e}")
            return {"error": str(e)}
    
    def _calculate_snr(self, audio_data: np.ndarray) -> float:
        """Calculate Signal-to-Noise Ratio"""
        try:
            # Simple SNR calculation
            signal_power = np.mean(audio_data ** 2)
            noise_estimate = np.var(audio_data)
            snr = 10 * np.log10(signal_power / (noise_estimate + 1e-10))
            return float(snr)
        except:
            return 0.0
    
    def _analyze_spectral_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Analyze spectral features of the audio"""
        try:
            # Compute spectrogram
            spec = np.abs(librosa.stft(audio_data))
            
            # Spectral centroid
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(S=spec))
            
            # Spectral bandwidth
            spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(S=spec))
            
            # Spectral rolloff
            spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(S=spec))
            
            # Spectral flatness
            spectral_flatness = np.mean(librosa.feature.spectral_flatness(S=spec))
            
            return {
                "spectral_centroid": float(spectral_centroid),
                "spectral_bandwidth": float(spectral_bandwidth),
                "spectral_rolloff": float(spectral_rolloff),
                "spectral_flatness": float(spectral_flatness)
            }
        except:
            return {}
    
    def _analyze_temporal_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Analyze temporal features of the audio"""
        try:
            # Root Mean Square Energy
            rms = np.sqrt(np.mean(audio_data ** 2))
            
            # Zero Crossing Rate
            zcr = np.mean(librosa.feature.zero_crossing_rate(audio_data))
            
            # Energy entropy
            frame_length = 2048
            hop_length = 512
            frames = librosa.util.frame(audio_data, frame_length=frame_length, hop_length=hop_length)
            frame_energy = np.sum(frames ** 2, axis=0)
            energy_entropy = -np.sum(frame_energy * np.log(frame_energy + 1e-10))
            
            return {
                "rms_energy": float(rms),
                "zero_crossing_rate": float(zcr),
                "energy_entropy": float(energy_entropy)
            }
        except:
            return {}
    
    def _analyze_energy_distribution(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Analyze energy distribution patterns"""
        try:
            # Frame the audio
            frame_length = 2048
            hop_length = 512
            frames = librosa.util.frame(audio_data, frame_length=frame_length, hop_length=hop_length)
            
            # Calculate frame energies
            frame_energies = np.sum(frames ** 2, axis=0)
            
            # Energy statistics
            energy_mean = np.mean(frame_energies)
            energy_std = np.std(frame_energies)
            energy_skewness = self._calculate_skewness(frame_energies)
            energy_kurtosis = self._calculate_kurtosis(frame_energies)
            
            # Energy variation
            energy_variation = energy_std / (energy_mean + 1e-10)
            
            return {
                "energy_mean": float(energy_mean),
                "energy_std": float(energy_std),
                "energy_skewness": float(energy_skewness),
                "energy_kurtosis": float(energy_kurtosis),
                "energy_variation": float(energy_variation)
            }
        except:
            return {}
    
    def _analyze_frequency_content(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Analyze frequency content characteristics"""
        try:
            # Mel-frequency cepstral coefficients (MFCC)
            mfccs = librosa.feature.mfcc(y=audio_data, sr=16000, n_mfcc=13)
            
            # MFCC statistics
            mfcc_mean = np.mean(mfccs, axis=1)
            mfcc_std = np.std(mfccs, axis=1)
            
            # Dominant frequency
            freqs = librosa.fft_frequencies(sr=16000)
            spec = np.abs(librosa.stft(audio_data))
            dominant_freq = freqs[np.argmax(np.mean(spec, axis=1))]
            
            # Frequency bandwidth
            freq_bandwidth = np.sum(spec > np.max(spec) * 0.5) / len(freqs)
            
            return {
                "mfcc_mean": mfcc_mean.tolist(),
                "mfcc_std": mfcc_std.tolist(),
                "dominant_frequency": float(dominant_freq),
                "frequency_bandwidth": float(freq_bandwidth)
            }
        except:
            return {}
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness of data"""
        try:
            mean = np.mean(data)
            std = np.std(data)
            if std == 0:
                return 0.0
            skewness = np.mean(((data - mean) / std) ** 3)
            return float(skewness)
        except:
            return 0.0
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of data"""
        try:
            mean = np.mean(data)
            std = np.std(data)
            if std == 0:
                return 0.0
            kurtosis = np.mean(((data - mean) / std) ** 4) - 3
            return float(kurtosis)
        except:
            return 0.0
    
    def _determine_risk_level(self, spoof_prob: float) -> str:
        """Determine risk level based on spoof probability"""
        if spoof_prob >= self.risk_thresholds["high_risk"]:
            return "HIGH"
        elif spoof_prob >= self.risk_thresholds["medium_risk"]:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_confidence(self, spoof_prob: float, audio_analysis: Dict[str, Any]) -> float:
        """Calculate confidence in the spoof detection result"""
        # Base confidence from AASIST
        base_confidence = 0.7
        
        # Additional confidence from audio analysis
        analysis_confidence = 0.0
        
        # Check if we have valid audio analysis
        if "error" not in audio_analysis:
            analysis_confidence += 0.2
            
            # Check SNR quality
            snr = audio_analysis.get("snr", 0)
            if snr > 20:  # Good SNR
                analysis_confidence += 0.1
            
            # Check spectral features
            if "spectral_features" in audio_analysis:
                analysis_confidence += 0.1
        
        return min(base_confidence + analysis_confidence, 1.0)
    
    def _identify_risk_factors(self, spoof_prob: float, audio_analysis: Dict[str, Any]) -> List[str]:
        """Identify specific risk factors for spoofing"""
        risk_factors = []
        
        # High spoof probability
        if spoof_prob > self.risk_thresholds["high_risk"]:
            risk_factors.append("High spoof probability detected")
        
        # Audio quality issues
        if "snr" in audio_analysis:
            snr = audio_analysis["snr"]
            if snr < 10:
                risk_factors.append("Poor audio quality (low SNR)")
        
        # Unusual spectral characteristics
        if "spectral_features" in audio_analysis:
            spec_features = audio_analysis["spectral_features"]
            if spec_features.get("spectral_flatness", 1.0) > 0.8:
                risk_factors.append("Unusual spectral flatness")
        
        # Energy distribution anomalies
        if "energy_distribution" in audio_analysis:
            energy_dist = audio_analysis["energy_distribution"]
            if energy_dist.get("energy_variation", 0) > 2.0:
                risk_factors.append("Irregular energy distribution")
        
        return risk_factors
    
    def batch_analyze(self, audio_files: List[bytes]) -> List[SpoofAnalysis]:
        """Analyze multiple audio files"""
        results = []
        for audio_bytes in audio_files:
            result = self.analyze_audio_authenticity(audio_bytes)
            results.append(result)
        return results


# Global anti-spoof detector instance
anti_spoof_detector = AntiSpoofDetector()


def detect_audio_spoofing(audio_bytes: bytes) -> Dict[str, Any]:
    """Main function to detect audio spoofing"""
    try:
        analysis = anti_spoof_detector.analyze_audio_authenticity(audio_bytes)
        
        return {
            "is_authentic": analysis.is_authentic,
            "spoof_probability": analysis.spoof_probability,
            "confidence": analysis.confidence,
            "risk_level": analysis.risk_level,
            "detection_method": analysis.detection_method,
            "analysis_details": analysis.analysis_details
        }
    except Exception as e:
        logger.error(f"Error in spoof detection: {e}")
        return {
            "error": "Spoof detection failed",
            "details": str(e),
            "is_authentic": False,
            "spoof_probability": 1.0,
            "confidence": 0.0,
            "risk_level": "HIGH"
        }


def get_spoof_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Get recommendations based on spoof analysis"""
    recommendations = []
    
    if not analysis.get("is_authentic", True):
        recommendations.append("🚨 HIGH RISK: Audio appears to be spoofed")
        recommendations.append("🚫 Do not trust this audio source")
        recommendations.append("🔍 Verify the caller's identity through other means")
        recommendations.append("📞 Report suspicious activity")
    
    elif analysis.get("risk_level") == "MEDIUM":
        recommendations.append("⚠️ MODERATE RISK: Exercise caution")
        recommendations.append("🔍 Verify audio source independently")
        recommendations.append("❓ Ask for alternative verification methods")
    
    else:
        recommendations.append("✅ LOW RISK: Audio appears authentic")
        recommendations.append("👂 Continue normal conversation")
    
    # Add specific recommendations based on analysis details
    details = analysis.get("analysis_details", {})
    if "risk_factors" in details:
        for factor in details["risk_factors"]:
            if "quality" in factor.lower():
                recommendations.append("🎵 Audio quality issues detected")
            elif "spectral" in factor.lower():
                recommendations.append("📊 Unusual audio characteristics")
            elif "energy" in factor.lower():
                recommendations.append("⚡ Irregular audio patterns")
    
    return recommendations
