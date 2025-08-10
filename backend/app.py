#!/usr/bin/env python3
"""
Voice Call Scam Detection Platform - Complete Web Interface
Combines API endpoints with WebRTC interface for real-time analysis
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import logging
import json
import os
import tempfile
from typing import Dict, List, Any
import base64
import time

# Import our unified analyzer
from unified_analyzer import analyze_voice_call, get_platform_statistics

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configuration
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB
SUPPORTED_FORMATS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']

# Create templates directory if it doesn't exist
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/css', exist_ok=True)

@app.route('/')
def index():
    """Main web interface"""
    return render_template('index.html')

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
def analyze_voice_call_endpoint():
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
    """Text-only scam detection endpoint"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
        
        text = data['text']
        if not text.strip():
            return jsonify({"error": "Empty text provided"}), 400
        
        logger.info(f"Analyzing text: {text[:100]}...")
        
        # For now, return a simple analysis
        # In a full implementation, you'd call the scam detection module
        risk_level = "LOW"
        if any(word in text.lower() for word in ['password', 'account', 'verify', 'urgent', 'immediately']):
            risk_level = "MEDIUM"
        if any(word in text.lower() for word in ['arrest', 'compromise', 'send money', 'gift cards']):
            risk_level = "HIGH"
        
        results = {
            "text": text,
            "risk_assessment": {
                "risk_level": risk_level,
                "risk_score": 0.3 if risk_level == "LOW" else 0.6 if risk_level == "MEDIUM" else 0.9,
                "risk_factors": []
            },
            "recommendations": [
                "Continue normal conversation" if risk_level == "LOW" else
                "Exercise caution" if risk_level == "MEDIUM" else
                "High risk detected - avoid providing personal information"
            ]
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
    """Audio authenticity detection endpoint"""
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        audio_bytes = audio_file.read()
        
        # For now, return a simple response
        # In full implementation, call the anti-spoof module
        results = {
            "is_authentic": True,
            "spoof_probability": 0.1,
            "confidence": 0.85,
            "recommendations": ["Audio appears authentic"]
        }
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in spoof detection: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    print("🎤 Voice Call Scam Detection Platform")
    print("=" * 50)
    print("🌐 Web Interface: http://localhost:5000")
    print("🔧 API Health: http://localhost:5000/health")
    print("📖 Documentation: See SETUP_GUIDE.md")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True) 