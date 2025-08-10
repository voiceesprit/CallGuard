# 🎤 Voice Call Scam Detection Platform - Complete Setup Guide

A comprehensive real-time platform for detecting scams during voice calls using advanced AI analysis.

## 🏗️ **Platform Overview**

This platform combines multiple AI models to provide real-time scam detection during voice calls:

- **🎯 Speech Recognition & Diarization** - Transcribes and identifies speakers
- **🛡️ Anti-spoof Detection** - Detects fake/recorded audio
- **🚨 Scam Detection** - Identifies scam patterns in speech
- **🤖 Bot Detection** - Detects automated/bot-like behavior
- **📊 Risk Assessment** - Provides unified risk scoring and recommendations

## 📋 **Prerequisites**

### **System Requirements**
- **OS**: Windows 10/11, macOS 10.15+, or Ubuntu 18.04+
- **Python**: 3.8 or higher
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: 10GB free space
- **GPU**: Optional but recommended (NVIDIA with 4GB+ VRAM)

### **Software Requirements**
- **Python 3.8+**
- **Node.js 14+** (for frontend)
- **FFmpeg** (for audio processing)
- **Git** (for cloning)

## 🚀 **Installation Steps**

### **Step 1: Clone the Repository**
```bash
git clone <your-repository-url>
cd voice-call-scam-detection
```

### **Step 2: Backend Setup**

#### **2.1 Install Python Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

#### **2.2 Install FFmpeg (if not already installed)**

**Windows:**
```bash
# Download from https://ffmpeg.org/download.html
# Or use chocolatey:
choco install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

#### **2.3 Download Required Models**
```bash
# The platform will automatically download models on first run
# This may take several minutes depending on your internet connection
```

### **Step 3: Frontend Setup**
```bash
cd frontend
npm install
```

## 🎮 **Running the Platform**

### **Option 1: Development Mode (Recommended for Testing)**

#### **Start Backend Server**
```bash
cd backend
python main.py
```
**Backend will run on:** `http://localhost:5000`

#### **Start Frontend Server**
```bash
cd frontend
node server.js
```
**Frontend will run on:** `http://localhost:3000`

### **Option 2: Production Mode**

#### **Using Gunicorn (Linux/macOS)**
```bash
cd backend
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

#### **Using PM2 (Node.js Process Manager)**
```bash
npm install -g pm2
cd frontend
pm2 start server.js --name "voice-call-frontend"
```

## 🔧 **Configuration**

### **Environment Variables**
Create a `.env` file in the backend directory:

```bash
# Backend Configuration
PORT=5000
DEBUG=False
MAX_AUDIO_SIZE=52428800  # 50MB
LOG_LEVEL=INFO

# Model Configuration
WHISPER_MODEL=small
USE_GPU=True
BATCH_SIZE=20

# Security
ENABLE_CORS=True
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### **Performance Tuning**
Edit `backend/asr.py` to adjust performance settings:

```python
# Performance configuration
BATCH_SIZE = 20  # Increase for faster processing
MAX_WORKERS = 2  # Adjust based on CPU cores
USE_GPU = True   # Set to False if no GPU
MEMORY_LIMIT = 0.8  # Use up to 80% of available memory
```

## 🧪 **Testing the Platform**

### **1. Health Check**
```bash
curl http://localhost:5000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "platform": "Voice Call Scam Detection Platform",
  "services": {
    "unified_analyzer": "available",
    "asr": "available",
    "scam_detection": "available",
    "anti_spoof": "available"
  },
  "statistics": {
    "total_analyses": 0,
    "total_processing_time": 0.0,
    "average_processing_time": 0.0,
    "platform_status": "operational"
  }
}
```

### **2. Test Voice Call Analysis**

#### **Using curl:**
```bash
curl -X POST http://localhost:5000/analyze_voice_call \
  -F "audio=@test_audio.mp3" \
  -F "call_id=test_call_001"
```

#### **Using Python:**
```python
import requests

# Test with audio file
with open('test_audio.mp3', 'rb') as f:
    files = {'audio': f}
    data = {'call_id': 'test_call_001'}
    response = requests.post('http://localhost:5000/analyze_voice_call', 
                           files=files, data=data)
    results = response.json()
    print(f"Risk Level: {results['overall_risk_level']}")
```

### **3. Test Text Analysis**
```bash
curl -X POST http://localhost:5000/analyze_text \
  -H "Content-Type: application/json" \
  -d '{"text": "Your account has been compromised. Send your password immediately."}'
```

## 📱 **Integration with Voice Calls**

### **Real-time Integration**

#### **WebRTC Integration (Frontend)**
```javascript
// Capture audio from WebRTC call
const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
const mediaRecorder = new MediaRecorder(audioStream);

mediaRecorder.ondataavailable = async (event) => {
    const audioBlob = event.data;
    
    // Send to backend for analysis
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('call_id', 'call_' + Date.now());
    
    const response = await fetch('/analyze_voice_call', {
        method: 'POST',
        body: formData
    });
    
    const results = await response.json();
    
    // Handle results
    if (results.overall_risk_level === 'HIGH') {
        showWarning('🚨 HIGH RISK DETECTED!');
    }
};
```

#### **SIP/VoIP Integration**
```python
# Example for SIP integration
import requests
import pjsua2 as pj

class CallHandler:
    def on_incoming_call(self, call):
        # Start recording
        call.record_call("temp_audio.wav")
        
    def on_call_ended(self, call):
        # Analyze recorded audio
        with open("temp_audio.wav", "rb") as f:
            files = {'audio': f}
            data = {'call_id': call.get_info().call_id}
            response = requests.post('http://localhost:5000/analyze_voice_call', 
                                   files=files, data=data)
            results = response.json()
            
            if results['overall_risk_level'] == 'HIGH':
                self.alert_security_team(results)
```

## 📊 **Understanding Results**

### **Risk Levels**
- **🟢 LOW (0.0-0.4)**: Safe to proceed
- **🟡 MEDIUM (0.4-0.7)**: Exercise caution
- **🔴 HIGH (0.7-1.0)**: High risk, avoid

### **Key Indicators**
- **Spoof Probability**: Likelihood of fake/recorded audio
- **Scam Score**: Probability of scam content
- **Bot Detection**: Whether speech patterns are human-like
- **Filler Words**: Indicates potential deception
- **Language Detection**: Multiple languages may indicate international scams

### **Sample Response**
```json
{
  "audio_duration": 45.2,
  "file_size_bytes": 1234567,
  "processing_time": 2.34,
  "transcript": "Hello, this is your bank calling...",
  
  "segments_count": 12,
  "languages_detected": ["en"],
  "translated_segments": 0,
  "is_authentic": true,
  "spoof_probability": 0.15,
  "spoof_confidence": 0.85,
  "is_scam": false,
  "scam_score": 0.12,
  "bot_or_human": "HUMAN-like",
  "perplexity": 45.2,
  "has_filler_words": false,
  "overall_risk_level": "LOW",
  "risk_score": 0.23,
  "risk_factors": [],
  "confidence": 0.78,
  "recommendations": [
    "✅ LOW RISK: No immediate concerns detected",
    "👂 Continue normal conversation",
    "🔍 Monitor for changes in behavior"
  ],
  "speaker_profiles": [...],
  "conversation_flow": {...},
  "analysis_timestamp": "2024-01-15 14:30:25"
}
```

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. Model Download Failures**
```bash
# Clear cache and retry
rm -rf ~/.cache/whisper
rm -rf ~/.cache/huggingface
```

#### **2. GPU Issues**
```bash
# Check CUDA installation
python -c "import torch; print(torch.cuda.is_available())"

# If no GPU, set USE_GPU=False in configuration
```

#### **3. Memory Issues**
```bash
# Reduce batch size in configuration
BATCH_SIZE = 10  # Instead of 20
```

#### **4. Audio Format Issues**
```bash
# Ensure FFmpeg is installed
ffmpeg -version

# Convert audio to supported format
ffmpeg -i input.wav -acodec pcm_s16le -ar 16000 output.wav
```

### **Logs and Debugging**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check backend logs
tail -f backend/logs/app.log

# Check frontend logs
pm2 logs voice-call-frontend
```

## 🚀 **Deployment Options**

### **1. Docker Deployment**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "main.py"]
```

### **2. Cloud Deployment**

#### **Railway**
```bash
# Connect to Railway
railway login
railway init
railway up
```

#### **Heroku**
```bash
# Create Procfile
echo "web: python main.py" > Procfile

# Deploy
heroku create
git push heroku main
```

#### **AWS EC2**
```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip ffmpeg

# Run with systemd
sudo systemctl enable voice-call-detection
sudo systemctl start voice-call-detection
```

## 📈 **Monitoring and Analytics**

### **Performance Monitoring**
```python
# Get platform statistics
import requests
stats = requests.get('http://localhost:5000/health').json()
print(f"Average processing time: {stats['statistics']['average_processing_time']:.2f}s")
```

### **Log Analysis**
```bash
# Monitor real-time logs
tail -f logs/app.log | grep "Risk Level"

# Analyze performance
grep "processing_time" logs/app.log | awk '{sum+=$NF; count++} END {print "Average:", sum/count}'
```

## 🔒 **Security Considerations**

### **Data Privacy**
- Audio is processed in memory, not stored
- Transcripts are not persisted
- All analysis is real-time

### **Access Control**
```python
# Add authentication to API
from functools import wraps
from flask import request, jsonify

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != 'your-secret-key':
            return jsonify({"error": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated_function
```

### **Rate Limiting**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

## 📞 **Support and Maintenance**

### **Regular Maintenance**
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Clear old logs
find logs/ -name "*.log" -mtime +30 -delete

# Check disk space
df -h
```

### **Backup Configuration**
```bash
# Backup important files
tar -czf backup-$(date +%Y%m%d).tar.gz \
    backend/config/ \
    backend/models/ \
    logs/
```

---

## 🎯 **Quick Start Checklist**

- [ ] Install Python 3.8+
- [ ] Install Node.js 14+
- [ ] Install FFmpeg
- [ ] Clone repository
- [ ] Install backend dependencies: `pip install -r requirements.txt`
- [ ] Install frontend dependencies: `npm install`
- [ ] Start backend: `python main.py`
- [ ] Start frontend: `node server.js`
- [ ] Test health endpoint: `curl http://localhost:5000/health`
- [ ] Test with sample audio file
- [ ] Configure for production deployment

**🎉 Your Voice Call Scam Detection Platform is now ready!** 
