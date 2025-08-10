# 🚀 Quick Start Guide - Voice Call Scam Detection Platform

## 🎯 **What You Get**

A complete web-based platform that analyzes voice calls in real-time to detect:
- 🚨 **Scam patterns** in speech
- 🎵 **Fake/recorded audio** (anti-spoof)
- 🤖 **Bot-like behavior** 
- 📊 **Risk assessment** with recommendations

## ⚡ **Start in 3 Steps**

### **Step 1: Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

### **Step 2: Start the Platform**
```bash
python start_platform.py
```

### **Step 3: Open Your Browser**
The platform will automatically open at: **http://localhost:5000**

## 🎮 **How to Use**

### **🌐 Web Interface Features**

#### **1. Real-time Voice Call Analysis**
- Click **"Start Call Analysis"** 
- Allow microphone access
- Speak or have a conversation
- Click **"Stop Analysis"** when done
- Get instant risk assessment

#### **2. Upload Audio Files**
- Click **"Choose Audio File"**
- Select MP3, WAV, M4A, FLAC, or OGG
- Click **"Analyze File"**
- View detailed results

#### **3. Text Analysis**
- Type or paste text in the text area
- Click **"Analyze Text"**
- Get scam detection results

### **📱 Real-time Features**

- **Live Risk Alerts**: High-risk calls trigger immediate notifications
- **Periodic Analysis**: Analyzes audio every 10 seconds during recording
- **Visual Indicators**: Color-coded risk levels (Green/Yellow/Red)
- **Detailed Reports**: Click "View Details" for comprehensive analysis

## 🔧 **API Usage**

### **Voice Call Analysis**
```bash
curl -X POST http://localhost:5000/analyze_voice_call \
  -F "audio=@your_audio.mp3" \
  -F "call_id=call_123"
```

### **Text Analysis**
```bash
curl -X POST http://localhost:5000/analyze_text \
  -H "Content-Type: application/json" \
  -d '{"text": "Your account has been compromised..."}'
```

### **Health Check**
```bash
curl http://localhost:5000/health
```

## 📊 **Understanding Results**

### **Risk Levels**
- 🟢 **LOW (0.0-0.4)**: Safe to proceed
- 🟡 **MEDIUM (0.4-0.7)**: Exercise caution  
- 🔴 **HIGH (0.7-1.0)**: High risk, avoid

### **Key Metrics**
- **Spoof Probability**: Likelihood of fake audio
- **Scam Score**: Probability of scam content
- **Bot Detection**: Human vs automated speech
- **Confidence**: Analysis reliability

### **Sample Response**
```json
{
  "overall_risk_level": "HIGH",
  "risk_score": 0.85,
  "is_scam": true,
  "is_authentic": false,
  "bot_or_human": "BOT-like",
  "recommendations": [
    "🚨 HIGH RISK: Exercise extreme caution",
    "🚫 Do not provide personal information",
    "📞 Report to authorities immediately"
  ]
}
```

## 🔗 **Integration Examples**

### **WebRTC Integration**
```javascript
// Capture audio from call
const mediaRecorder = new MediaRecorder(audioStream);
mediaRecorder.ondataavailable = async (event) => {
    const formData = new FormData();
    formData.append('audio', event.data);
    formData.append('call_id', 'call_' + Date.now());
    
    const response = await fetch('/analyze_voice_call', {
        method: 'POST',
        body: formData
    });
    
    const results = await response.json();
    if (results.overall_risk_level === 'HIGH') {
        showWarning('🚨 HIGH RISK DETECTED!');
    }
};
```

### **SIP/VoIP Integration**
```python
import requests

def analyze_call_audio(audio_file, call_id):
    with open(audio_file, 'rb') as f:
        files = {'audio': f}
        data = {'call_id': call_id}
        response = requests.post('http://localhost:5000/analyze_voice_call', 
                               files=files, data=data)
        results = response.json()
        
        if results['overall_risk_level'] == 'HIGH':
            alert_security_team(results)
        
        return results
```

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **1. "Microphone Error"**
- Check browser permissions
- Allow microphone access when prompted
- Try refreshing the page

#### **2. "Analysis Failed"**
- Check if audio file is supported format
- Ensure file size < 50MB
- Verify FFmpeg is installed

#### **3. "Connection Failed"**
- Ensure backend is running on port 5000
- Check firewall settings
- Try restarting the platform

### **Performance Tips**
- Use GPU for faster processing (automatic detection)
- Keep audio files under 10MB for quick analysis
- Close other applications to free up memory

## 📈 **Production Deployment**

### **Using Gunicorn**
```bash
cd backend
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### **Using Docker**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### **Environment Variables**
```bash
export PORT=5000
export DEBUG=False
export MAX_AUDIO_SIZE=52428800
export USE_GPU=True
```

## 🎯 **Next Steps**

1. **Test with Sample Audio**: Try uploading different audio files
2. **Integrate with Your System**: Use the API endpoints
3. **Customize Analysis**: Modify risk thresholds and detection rules
4. **Deploy to Production**: Set up monitoring and alerts
5. **Train Custom Models**: Add your own scam patterns

## 📞 **Support**

- **Documentation**: See `SETUP_GUIDE.md` for detailed setup
- **API Reference**: All endpoints documented in the guide
- **Testing**: Use `test_platform.py` to verify functionality
- **Issues**: Check logs in the browser console

---

## 🎉 **You're Ready!**

Your Voice Call Scam Detection Platform is now running and ready to protect against scams in real-time! 

**🌐 Open http://localhost:5000 and start analyzing voice calls!** 