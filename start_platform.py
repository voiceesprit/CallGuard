#!/usr/bin/env python3
"""
Voice Call Scam Detection Platform - Startup Script
Simple script to start the complete platform with web interface
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import flask
        import torch
        import numpy
        print("✅ All Python dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies: pip install -r backend/requirements.txt")
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg is installed")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("⚠️  FFmpeg not found. Audio processing may not work properly.")
    print("   Install FFmpeg: https://ffmpeg.org/download.html")
    return False

def start_server():
    """Start the Flask server"""
    print("🚀 Starting Voice Call Scam Detection Platform...")
    print("=" * 60)
    
    # Change to backend directory
    os.chdir('backend')
    
    # Start the Flask app
    try:
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        return False
    
    return True

def open_browser():
    """Open browser after a short delay"""
    time.sleep(3)  # Wait for server to start
    try:
        webbrowser.open('http://localhost:5000')
        print("🌐 Opening web interface in browser...")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print("   Please open: http://localhost:5000")

def main():
    """Main startup function"""
    print("🎤 Voice Call Scam Detection Platform")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check FFmpeg
    check_ffmpeg()
    
    print("\n📋 Platform Features:")
    print("   • Real-time voice call analysis")
    print("   • WebRTC microphone integration")
    print("   • Audio file upload and analysis")
    print("   • Text analysis for scam detection")
    print("   • Anti-spoof detection")
    print("   • Bot detection")
    print("   • Risk assessment and recommendations")
    
    print("\n🌐 Web Interface will be available at:")
    print("   http://localhost:5000")
    
    print("\n📖 API Endpoints:")
    print("   • GET  /health - Health check")
    print("   • POST /analyze_voice_call - Voice call analysis")
    print("   • POST /analyze_text - Text analysis")
    print("   • POST /detect_spoof - Audio authenticity")
    
    print("\n" + "=" * 60)
    
    # Start browser in background thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start server
    return start_server()

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Platform stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1) 