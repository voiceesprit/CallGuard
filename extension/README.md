# CallGuard Extension

A browser extension for real-time scam detection during voice calls with early risk scoring.

## Features

- **Real-time Audio Analysis**: Continuously monitors microphone input during calls
- **Early Risk Assessment**: Provides immediate risk scores based on audio features
- **Multi-language Support**: Detects scam keywords in English, Spanish, French, German, and Chinese
- **Webpage Integration**: Highlights suspicious form fields and shows risk indicators
- **Backend Integration**: Sends audio data to backend for comprehensive analysis
- **Real-time Alerts**: Immediate notifications for high-risk situations

## Prerequisites

- Node.js and npm installed
- TypeScript compiler (`tsc`)
- A running backend server at `http://localhost:5000`

## Building the Extension

### Option 1: Using PowerShell (Recommended for Windows)
```powershell
.\build.ps1
```

### Option 2: Using Command Prompt
```cmd
.\build.bat
```

### Option 3: Manual Build
```bash
# Install TypeScript globally if not already installed
npm install -g typescript

# Compile TypeScript files
tsc

# Copy compiled JavaScript files to extension root
copy src\*.js .
```

## Installation in Edge/Chrome

1. **Build the extension** using one of the methods above
2. **Open Edge/Chrome** and navigate to `edge://extensions/` or `chrome://extensions/`
3. **Enable Developer Mode** (toggle switch in top right)
4. **Click "Load unpacked"** and select the `extension` folder
5. **Grant permissions** when prompted (microphone access, etc.)

## Extension Structure

```
extension/
├── manifest.json          # Extension configuration
├── popup.html            # Popup interface
├── popup.js              # Popup functionality
├── popup.css             # Popup styling
├── content.js            # Content script for webpage integration
├── src/
│   ├── background.ts     # Background service worker
│   ├── audioProcessor.ts # Audio processing and analysis
│   ├── communicationService.ts # Backend communication
│   ├── config.ts         # Configuration management
│   └── types.ts          # TypeScript type definitions
├── build.bat             # Windows build script
├── build.ps1             # PowerShell build script
└── package.json          # Dependencies and scripts
```

## How It Works

### 1. **Activation**
- User enables protection via popup toggle
- Extension requests microphone permission
- Background service starts audio recording
- WebSocket connection established with backend

### 2. **Real-time Processing**
- Audio captured in 3-second chunks
- Features extracted: speaking rate, stress, synthetic voice likelihood
- Risk score calculated (0-100)
- Data sent to backend for analysis
- Alerts shown for medium/high risk scores

### 3. **Webpage Integration**
- Content script injects into all web pages
- Highlights suspicious form fields (SSN, credit card, etc.)
- Shows risk indicators during calls
- Enables webpage-to-extension communication

### 4. **Risk Scoring System**
- **Keywords (40%)**: Scam-related phrases in multiple languages
- **Speaking Rate (15%)**: Speech pattern analysis
- **Stress Level (15%)**: Volume and frequency analysis
- **Synthetic Voice (20%)**: AI-generated voice detection
- **Language Confidence (10%)**: Language detection certainty

## Configuration

The extension can be configured via the `config.ts` file:

- **Risk Thresholds**: Low (30), Medium (60), High (80)
- **Chunk Duration**: Audio processing interval (default: 3 seconds)
- **Keywords**: Multi-language scam detection phrases
- **Backend URLs**: WebSocket and HTTP endpoints

## Troubleshooting

### Common Issues

1. **"Extension not loading"**
   - Ensure all files are compiled and present
   - Check browser console for errors
   - Verify manifest.json syntax

2. **"Microphone access denied"**
   - Check browser permissions
   - Ensure microphone is not used by other applications
   - Try refreshing the page

3. **"Backend connection failed"**
   - Verify backend server is running at localhost:5000
   - Check firewall settings
   - Test connection via popup button

4. **"TypeScript compilation errors"**
   - Install TypeScript: `npm install -g typescript`
   - Check for syntax errors in .ts files
   - Verify tsconfig.json configuration

### Debug Mode

Enable debug logging by opening the browser console and looking for "CallGuard" messages.

## Development

### Adding New Features

1. **New Audio Features**: Extend `EarlyRiskFeatures` interface in `types.ts`
2. **New Languages**: Add keywords to `config.ts`
3. **New Risk Factors**: Modify `calculateRiskScore()` in `audioProcessor.ts`
4. **UI Changes**: Update `popup.html` and `popup.js`

### Testing

1. **Build and load** the extension
2. **Open a test page** with forms
3. **Enable protection** and start speaking
4. **Monitor console** for debug messages
5. **Check popup** for status updates

## Backend Integration

The extension expects a backend server with:

- **WebSocket endpoint**: `ws://localhost:5000/ws`
- **HTTP API endpoints**: `/api/audio_chunk`, `/api/risk_score`
- **Session management**: Start/end session handling
- **Audio processing**: Chunk analysis and storage

## License

This extension is part of the CallGuard project for scam detection and prevention.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review browser console for error messages
3. Verify backend server status
4. Check extension permissions in browser settings 