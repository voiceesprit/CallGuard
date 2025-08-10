#!/usr/bin/env python3
"""
Main API Server for Audio Analysis and Scam Detection
Integrates ASR, scam detection, and anti-spoof capabilities
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import json
import os
import tempfile
from typing import Dict, List, Any
import base64

# Import our modules
from unified_analyzer import analyze_voice_call, get_platform_statistics

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB limit
SUPPORTED_FORMATS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    stats = get_platform_statistics()
    return jsonify({
        "status": "healthy",
        "platform": "Voice Call Scam Detection Platform",
        "services": {
            "unified_analyzer": "available",
            "asr": "available",
            "scam_detection": "available", 
            "anti_spoof": "available"
        },
        "statistics": stats
    })


@app.route('/analyze_voice_call', methods=['POST'])
def analyze_voice_call():
    """
    Main endpoint for comprehensive voice call analysis
    Expects: multipart/form-data with audio file or base64 encoded audio
    """
    try:
        # Check if audio is provided
        if 'audio' not in request.files and 'audio_base64' not in request.form:
            return jsonify({
                "error": "No audio provided. Send 'audio' file or 'audio_base64' string"
            }), 400
        
        # Get call ID if provided
        call_id = request.form.get('call_id', None)
        
        # Get audio data
        audio_bytes = None
        
        if 'audio' in request.files:
            # Handle file upload
            audio_file = request.files['audio']
            if audio_file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            # Check file size
            audio_file.seek(0, 2)  # Seek to end
            file_size = audio_file.tell()
            audio_file.seek(0)  # Reset to beginning
            
            if file_size > MAX_AUDIO_SIZE:
                return jsonify({
                    "error": f"File too large. Maximum size: {MAX_AUDIO_SIZE // (1024*1024)}MB"
                }), 400
            
            # Check file format
            file_ext = os.path.splitext(audio_file.filename)[1].lower()
            if file_ext not in SUPPORTED_FORMATS:
                return jsonify({
                    "error": f"Unsupported format. Supported: {', '.join(SUPPORTED_FORMATS)}"
                }), 400
            
            audio_bytes = audio_file.read()
            
        elif 'audio_base64' in request.form:
            # Handle base64 encoded audio
            try:
                audio_base64 = request.form['audio_base64']
                audio_bytes = base64.b64decode(audio_base64)
                
                if len(audio_bytes) > MAX_AUDIO_SIZE:
                    return jsonify({
                        "error": f"Audio too large. Maximum size: {MAX_AUDIO_SIZE // (1024*1024)}MB"
                    }), 400
                    
            except Exception as e:
                return jsonify({"error": f"Invalid base64 audio: {str(e)}"}), 400
        
        if not audio_bytes:
            return jsonify({"error": "No valid audio data provided"}), 400
        
        logger.info(f"Processing voice call {call_id}: {len(audio_bytes)} bytes")
        
        # Run unified analysis
        results = analyze_voice_call(audio_bytes, call_id)
        
        logger.info(f"Voice call analysis completed for {call_id}")
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in voice call analysis: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500


@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    """
    Analyze text for scam detection without audio processing
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
        
        text = data['text']
        if not text.strip():
            return jsonify({"error": "Empty text provided"}), 400
        
        # Run scam detection
        scam_results = detect_scam_and_bot(text)
        
        results = {
            "text_analysis": {
                "text_length": len(text),
                "word_count": len(text.split())
            },
            "scam_detection": {
                "is_scam": scam_results["scam"] == "YES",
                "scam_score": scam_results["combined_scam_score"],
                "bot_or_human": scam_results["bot_or_human"],
                "perplexity": scam_results["perplexity"],
                "detected_language": scam_results["lang"],
                "has_filler_words": scam_results["has_filler"]
            },
            "risk_assessment": {
                "risk_level": _get_risk_level(scam_results["combined_scam_score"]),
                "recommendations": _get_recommendations(scam_results)
            }
        }
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in text analysis: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500


@app.route('/detect_spoof', methods=['POST'])
def detect_spoof():
    """
    Anti-spoof detection endpoint
    """
    try:
        if 'audio' not in request.files and 'audio_base64' not in request.form:
            return jsonify({
                "error": "No audio provided. Send 'audio' file or 'audio_base64' string"
            }), 400
        
        # Get audio data
        audio_bytes = None
        
        if 'audio' in request.files:
            audio_file = request.files['audio']
            audio_bytes = audio_file.read()
        elif 'audio_base64' in request.form:
            audio_base64 = request.form['audio_base64']
            audio_bytes = base64.b64decode(audio_base64)
        
        if not audio_bytes:
            return jsonify({"error": "No valid audio data provided"}), 400
        
        # Run anti-spoof detection
        spoof_prob, spoof_label = detect_spoof_from_bytes(audio_bytes)
        
        results = {
            "spoof_probability": spoof_prob,
            "spoof_label": spoof_label,
            "is_authentic": spoof_label == "BONAFIDE",
            "confidence": 1.0 - spoof_prob if spoof_label == "BONAFIDE" else spoof_prob
        }
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in spoof detection: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500


def _calculate_overall_risk(spoof_prob: float, scam_score: float, bot_human: str) -> str:
    """Calculate overall risk level based on all factors"""
    risk_score = 0.0
    
    # Anti-spoof risk (higher spoof probability = higher risk)
    risk_score += spoof_prob * 0.4
    
    # Scam risk
    risk_score += scam_score * 0.4
    
    # Bot risk (bot-like behavior = higher risk)
    if bot_human == "BOT-like":
        risk_score += 0.2
    
    # Determine risk level
    if risk_score >= 0.7:
        return "HIGH"
    elif risk_score >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"


def _identify_risk_factors(spoof_prob: float, scam_results: Dict, speaker_analysis: Dict) -> List[str]:
    """Identify specific risk factors"""
    risk_factors = []
    
    if spoof_prob > 0.5:
        risk_factors.append("Potential audio spoofing detected")
    
    if scam_results["combined_scam_score"] > 0.6:
        risk_factors.append("High scam probability")
    
    if scam_results["bot_or_human"] == "BOT-like":
        risk_factors.append("Bot-like speech patterns detected")
    
    if scam_results["has_filler"]:
        risk_factors.append("Filler words detected (potential deception)")
    
    if len(speaker_analysis.get("languages", [])) > 1:
        risk_factors.append("Multiple languages detected")
    
    if speaker_analysis.get("translated_segments", 0) > 0:
        risk_factors.append("Translated content detected")
    
    return risk_factors


def _get_risk_level(scam_score: float) -> str:
    """Get risk level based on scam score"""
    if scam_score >= 0.7:
        return "HIGH"
    elif scam_score >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"


def _get_recommendations(scam_results: Dict) -> List[str]:
    """Get recommendations based on analysis results"""
    recommendations = []
    
    if scam_results["scam"] == "YES":
        recommendations.append("⚠️ HIGH RISK: This appears to be a scam attempt")
        recommendations.append("🚫 Do not provide personal or financial information")
        recommendations.append("📞 Report to authorities if necessary")
    
    if scam_results["bot_or_human"] == "BOT-like":
        recommendations.append("🤖 Bot-like patterns detected - exercise caution")
    
    if scam_results["has_filler"]:
        recommendations.append("💬 Filler words detected - speaker may be deceptive")
    
    if scam_results["combined_scam_score"] > 0.3:
        recommendations.append("🔍 Moderate risk - verify the source independently")
    
    if not recommendations:
        recommendations.append("✅ No immediate risks detected")
    
    return recommendations


if __name__ == '__main__':
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
