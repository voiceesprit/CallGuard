// Voice Call Scam Detection Platform - WebRTC Interface

class VoiceCallAnalyzer {
    constructor() {
        this.mediaRecorder = null;
        this.audioStream = null;
        this.isRecording = false;
        this.analysisInterval = null;
        this.chunks = [];
        this.callId = null;
        
        this.initializeElements();
        this.bindEvents();
        this.checkConnection();
    }

    initializeElements() {
        // Control buttons
        this.startCallBtn = document.getElementById('startCall');
        this.stopCallBtn = document.getElementById('stopCall');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.analyzeFileBtn = document.getElementById('analyzeFile');
        this.analyzeTextBtn = document.getElementById('analyzeText');
        this.clearResultsBtn = document.getElementById('clearResults');
        
        // File upload
        this.audioFileInput = document.getElementById('audioFile');
        this.fileNameSpan = document.getElementById('fileName');
        
        // Text analysis
        this.textInput = document.getElementById('textInput');
        
        // Status and results
        this.callStatus = document.getElementById('callStatus');
        this.resultsContent = document.getElementById('resultsContent');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusDot = this.statusIndicator.querySelector('.status-dot');
        this.statusText = this.statusIndicator.querySelector('.status-text');
        
        // Risk indicator
        this.riskIndicator = document.getElementById('riskIndicator');
        this.riskTitle = document.getElementById('riskTitle');
        this.riskDescription = document.getElementById('riskDescription');
        this.viewDetailsBtn = document.getElementById('viewDetails');
        this.dismissRiskBtn = document.getElementById('dismissRisk');
        
        // Loading overlay
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.loadingMessage = document.getElementById('loadingMessage');
        
        // Modal
        this.resultsModal = document.getElementById('resultsModal');
        this.modalBody = document.getElementById('modalBody');
        this.closeModalBtn = document.getElementById('closeModal');
    }

    bindEvents() {
        // Call control
        this.startCallBtn.addEventListener('click', () => this.startCallAnalysis());
        this.stopCallBtn.addEventListener('click', () => this.stopCallAnalysis());
        
        // File upload
        this.uploadBtn.addEventListener('click', () => this.audioFileInput.click());
        this.audioFileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.analyzeFileBtn.addEventListener('click', () => this.analyzeAudioFile());
        
        // Text analysis
        this.analyzeTextBtn.addEventListener('click', () => this.analyzeText());
        
        // Results
        this.clearResultsBtn.addEventListener('click', () => this.clearResults());
        
        // Risk indicator
        this.viewDetailsBtn.addEventListener('click', () => this.showDetailedResults());
        this.dismissRiskBtn.addEventListener('click', () => this.hideRiskIndicator());
        
        // Modal
        this.closeModalBtn.addEventListener('click', () => this.closeModal());
        this.resultsModal.addEventListener('click', (e) => {
            if (e.target === this.resultsModal) this.closeModal();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'Enter':
                        if (this.textInput === document.activeElement) {
                            e.preventDefault();
                            this.analyzeText();
                        }
                        break;
                    case 'Escape':
                        this.closeModal();
                        this.hideRiskIndicator();
                        break;
                }
            }
        });
    }

    async checkConnection() {
        try {
            const response = await fetch('/health');
            if (response.ok) {
                this.updateStatus('connected', 'Connected');
            } else {
                this.updateStatus('error', 'Server Error');
            }
        } catch (error) {
            this.updateStatus('error', 'Connection Failed');
        }
    }

    updateStatus(type, text) {
        this.statusText.textContent = text;
        this.statusDot.className = 'status-dot ' + type;
    }

    async startCallAnalysis() {
        try {
            this.updateStatus('connecting', 'Requesting Microphone...');
            
            // Request microphone access
            this.audioStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000
                } 
            });
            
            // Create media recorder
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.callId = 'call_' + Date.now();
            this.chunks = [];
            
            // Set up recording events
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.chunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstart = () => {
                this.isRecording = true;
                this.startCallBtn.disabled = true;
                this.stopCallBtn.disabled = false;
                this.callStatus.innerHTML = '<p><i class="fas fa-microphone"></i> Recording in progress... Click "Stop Analysis" to analyze the call.</p>';
                this.updateStatus('connected', 'Recording');
                
                // Start periodic analysis
                this.startPeriodicAnalysis();
            };
            
            this.mediaRecorder.onstop = () => {
                this.isRecording = false;
                this.stopCallBtn.disabled = true;
                this.startCallBtn.disabled = false;
                this.callStatus.innerHTML = '<p>Recording stopped. Analyzing call...</p>';
                this.updateStatus('connecting', 'Analyzing...');
                
                // Analyze the recorded audio
                this.analyzeRecordedAudio();
            };
            
            // Start recording
            this.mediaRecorder.start(1000); // Collect data every second
            
        } catch (error) {
            console.error('Error starting call analysis:', error);
            this.updateStatus('error', 'Microphone Error');
            this.callStatus.innerHTML = '<p style="color: #ff6b6b;">Error: Could not access microphone. Please check permissions.</p>';
        }
    }

    stopCallAnalysis() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.audioStream.getTracks().forEach(track => track.stop());
            this.stopPeriodicAnalysis();
        }
    }

    startPeriodicAnalysis() {
        // Analyze audio every 10 seconds during recording
        this.analysisInterval = setInterval(async () => {
            if (this.chunks.length > 0) {
                const audioBlob = new Blob(this.chunks, { type: 'audio/webm' });
                await this.analyzeAudioChunk(audioBlob, true); // Real-time analysis
            }
        }, 10000); // Every 10 seconds
    }

    stopPeriodicAnalysis() {
        if (this.analysisInterval) {
            clearInterval(this.analysisInterval);
            this.analysisInterval = null;
        }
    }

    async analyzeRecordedAudio() {
        if (this.chunks.length === 0) {
            this.callStatus.innerHTML = '<p>No audio recorded.</p>';
            this.updateStatus('connected', 'Connected');
            return;
        }

        const audioBlob = new Blob(this.chunks, { type: 'audio/webm' });
        await this.analyzeAudioChunk(audioBlob, false); // Full analysis
    }

    async analyzeAudioChunk(audioBlob, isRealTime = false) {
        try {
            this.showLoading(isRealTime ? 'Analyzing live audio...' : 'Processing recorded call...');
            
            const formData = new FormData();
            formData.append('audio', audioBlob);
            formData.append('call_id', this.callId);
            
            const response = await fetch('/analyze_voice_call', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const results = await response.json();
            this.hideLoading();
            
            if (isRealTime) {
                this.handleRealTimeResults(results);
            } else {
                this.displayResults(results);
            }
            
        } catch (error) {
            console.error('Error analyzing audio:', error);
            this.hideLoading();
            this.callStatus.innerHTML = '<p style="color: #ff6b6b;">Error analyzing audio: ' + error.message + '</p>';
            this.updateStatus('error', 'Analysis Failed');
        }
    }

    handleRealTimeResults(results) {
        const riskLevel = results.overall_risk_level;
        
        if (riskLevel === 'HIGH') {
            this.showRiskIndicator('HIGH RISK DETECTED!', '🚨 Immediate action required', results);
        } else if (riskLevel === 'MEDIUM') {
            this.showRiskIndicator('MEDIUM RISK DETECTED', '⚠️ Exercise caution', results);
        }
        
        // Update call status with brief info and transcript preview
        let transcriptPreview = 'No transcript yet';
        if (results.transcript) {
            const lines = results.transcript.split('\n');
            if (lines.length > 0) {
                const lastLine = lines[lines.length - 1];
                transcriptPreview = lastLine.substring(0, 100) + (lastLine.length > 100 ? '...' : '');
            }
        }
            
        this.callStatus.innerHTML = `
            <p><i class="fas fa-microphone"></i> Recording in progress... 
            <span style="color: ${riskLevel === 'HIGH' ? '#ff6b6b' : riskLevel === 'MEDIUM' ? '#ffd93d' : '#51cf66'}">
                Risk Level: ${riskLevel}
            </span>
            </p>
            <div style="margin-top: 10px; padding: 10px; background: rgba(255,255,255,0.8); border-radius: 8px; font-size: 0.9em;">
                <strong>📝 Live Transcript:</strong> ${transcriptPreview}
            </div>
        `;
    }

    displayResults(results) {
        const resultElement = this.createResultElement(results);
        this.resultsContent.insertBefore(resultElement, this.resultsContent.firstChild);
        
        this.callStatus.innerHTML = '<p>Analysis completed successfully!</p>';
        this.updateStatus('connected', 'Connected');
        
        // Show risk indicator if high risk
        if (results.overall_risk_level === 'HIGH') {
            this.showRiskIndicator('HIGH RISK DETECTED!', '🚨 Immediate action required', results);
        }
    }

    createResultElement(results) {
        const riskClass = results.overall_risk_level.toLowerCase() + '-risk';
        const riskIcon = results.overall_risk_level === 'HIGH' ? '🚨' : 
                        results.overall_risk_level === 'MEDIUM' ? '⚠️' : '✅';
        
        const resultHtml = `
            <div class="analysis-result ${riskClass}" data-results='${JSON.stringify(results)}'>
                <div class="result-header">
                    <div class="result-title">
                        ${riskIcon} Voice Call Analysis
                    </div>
                    <div class="result-time">
                        ${new Date().toLocaleTimeString()}
                    </div>
                </div>
                
                <div class="risk-level ${results.overall_risk_level.toLowerCase()}">
                    <i class="fas fa-shield-alt"></i>
                    ${results.overall_risk_level} RISK
                </div>
                
                <div class="result-details">
                    <div class="detail-item">
                        <div class="detail-label">Processing Time</div>
                        <div class="detail-value">${results.processing_time?.toFixed(2) || 'N/A'}s</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Audio Duration</div>
                        <div class="detail-value">${results.audio_duration?.toFixed(1) || 'N/A'}s</div>
                    </div>
                    <div class="detail-item">
                        
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Confidence</div>
                        <div class="detail-value">${(results.confidence * 100)?.toFixed(1) || 'N/A'}%</div>
                    </div>
                </div>
                
                <div class="recommendations">
                    <h4>Recommendations:</h4>
                    <ul>
                        ${results.recommendations?.map(rec => `<li>${rec}</li>`).join('') || '<li>No specific recommendations</li>'}
                    </ul>
                </div>
                
                                  <div class="transcript-section">
                      <h4>Transcript:</h4>
                      <div class="transcript-content">
                          ${results.transcript ? results.transcript.split('\n').map(line => {
                              return `<div class="transcript-line">${line}</div>`;
                          }).join('') : 'No transcript available'}
                      </div>
                  </div>
            </div>
        `;
        
        const div = document.createElement('div');
        div.innerHTML = resultHtml;
        return div.firstElementChild;
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.fileNameSpan.textContent = file.name;
            this.analyzeFileBtn.disabled = false;
        } else {
            this.fileNameSpan.textContent = 'No file selected';
            this.analyzeFileBtn.disabled = true;
        }
    }

    async analyzeAudioFile() {
        const file = this.audioFileInput.files[0];
        if (!file) return;

        try {
            this.showLoading('Analyzing audio file...');
            
            const formData = new FormData();
            formData.append('audio', file);
            formData.append('call_id', 'file_' + Date.now());
            
            const response = await fetch('/analyze_voice_call', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const results = await response.json();
            this.hideLoading();
            this.displayResults(results);
            
        } catch (error) {
            console.error('Error analyzing file:', error);
            this.hideLoading();
            alert('Error analyzing file: ' + error.message);
        }
    }

    async analyzeText() {
        const text = this.textInput.value.trim();
        if (!text) {
            alert('Please enter some text to analyze.');
            return;
        }

        try {
            this.showLoading('Analyzing text...');
            
            const response = await fetch('/analyze_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const results = await response.json();
            this.hideLoading();
            
            // Create a simplified result for text analysis
            const textResult = {
                overall_risk_level: results.risk_assessment.risk_level,
                processing_time: 0.5,
                audio_duration: 0,

                confidence: 0.8,
                transcript: text,
                recommendations: results.recommendations,
                analysis_timestamp: new Date().toISOString()
            };
            
            this.displayResults(textResult);
            
        } catch (error) {
            console.error('Error analyzing text:', error);
            this.hideLoading();
            alert('Error analyzing text: ' + error.message);
        }
    }

    showRiskIndicator(title, description, results) {
        this.riskTitle.textContent = title;
        this.riskDescription.textContent = description;
        this.riskIndicator.dataset.results = JSON.stringify(results);
        this.riskIndicator.style.display = 'block';
        
        // Auto-hide after 10 seconds for medium risk
        if (results.overall_risk_level === 'MEDIUM') {
            setTimeout(() => this.hideRiskIndicator(), 10000);
        }
    }

    hideRiskIndicator() {
        this.riskIndicator.style.display = 'none';
    }

    showDetailedResults() {
        const results = JSON.parse(this.riskIndicator.dataset.results);
        this.showModal(results);
    }

    showModal(results) {
        const modalHtml = this.createDetailedModalContent(results);
        this.modalBody.innerHTML = modalHtml;
        this.resultsModal.style.display = 'flex';
    }

    createDetailedModalContent(results) {
        return `
            <div class="detailed-results">
                <div class="section">
                    <h4>📊 Analysis Summary</h4>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <strong>Risk Level:</strong> 
                            <span class="risk-badge ${results.overall_risk_level.toLowerCase()}">${results.overall_risk_level}</span>
                        </div>
                        <div class="summary-item">
                            <strong>Risk Score:</strong> ${(results.risk_score * 100).toFixed(1)}%
                        </div>
                        <div class="summary-item">
                            <strong>Confidence:</strong> ${(results.confidence * 100).toFixed(1)}%
                        </div>
                        <div class="summary-item">
                            <strong>Processing Time:</strong> ${results.processing_time?.toFixed(2) || 'N/A'}s
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h4>🎵 Audio Analysis</h4>
                    <div class="detail-grid">
                        <div><strong>Duration:</strong> ${results.audio_duration?.toFixed(1) || 'N/A'}s</div>
                        <div><strong>File Size:</strong> ${(results.file_size_bytes / 1024 / 1024).toFixed(2)} MB</div>
        
                        <div><strong>Segments:</strong> ${results.segments_count || 'N/A'}</div>
                        <div><strong>Languages:</strong> ${results.languages_detected?.join(', ') || 'N/A'}</div>
                    </div>
                </div>
                
                <div class="section">
                    <h4>🛡️ Security Analysis</h4>
                    <div class="detail-grid">
                        <div><strong>Authentic Audio:</strong> ${results.is_authentic ? '✅ Yes' : '❌ No'}</div>
                        <div><strong>Spoof Probability:</strong> ${(results.spoof_probability * 100).toFixed(1)}%</div>
                        <div><strong>Scam Detected:</strong> ${results.is_scam ? '🚨 Yes' : '✅ No'}</div>
                        <div><strong>Scam Score:</strong> ${(results.scam_score * 100).toFixed(1)}%</div>
                        <div><strong>Bot/Human:</strong> ${results.bot_or_human}</div>
                        <div><strong>Filler Words:</strong> ${results.has_filler_words ? '⚠️ Yes' : '✅ No'}</div>
                    </div>
                </div>
                
                <div class="section">
                    <h4>⚠️ Risk Factors</h4>
                    <ul class="risk-factors">
                        ${results.risk_factors?.map(factor => `<li>${factor}</li>`).join('') || '<li>No specific risk factors identified</li>'}
                    </ul>
                </div>
                
                <div class="section">
                                          <h4>📝 Transcript</h4>
                      <div class="transcript">
                          ${results.transcript ? results.transcript.split('\n').map(line => {
                              return `<div class="transcript-line">${line}</div>`;
                          }).join('') : 'No transcript available'}
                      </div>
                </div>
                
                <div class="section">
                    <h4>💡 Recommendations</h4>
                    <ul class="recommendations-list">
                        ${results.recommendations?.map(rec => `<li>${rec}</li>`).join('') || '<li>No specific recommendations</li>'}
                    </ul>
                </div>
            </div>
        `;
    }

    closeModal() {
        this.resultsModal.style.display = 'none';
    }

    clearResults() {
        this.resultsContent.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-info-circle"></i>
                <h4>Welcome to Voice Call Scam Detection</h4>
                <p>This platform analyzes voice calls in real-time to detect potential scams, spoofed audio, and suspicious behavior.</p>
                <div class="features">
                    <div class="feature">
                        <i class="fas fa-microphone"></i>
                        <span>Real-time Voice Analysis</span>
                    </div>
                    <div class="feature">
                        <i class="fas fa-shield-alt"></i>
                        <span>Anti-spoof Detection</span>
                    </div>
                    <div class="feature">
                        <i class="fas fa-robot"></i>
                        <span>Bot Detection</span>
                    </div>
                    <div class="feature">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>Scam Pattern Recognition</span>
                    </div>
                    <div class="feature">
                        <i class="fas fa-file-alt"></i>
                        <span>Full Transcript Generation</span>
                    </div>
                </div>
            </div>
        `;
    }

    showLoading(message) {
        this.loadingMessage.textContent = message;
        this.loadingOverlay.style.display = 'flex';
    }

    hideLoading() {
        this.loadingOverlay.style.display = 'none';
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new VoiceCallAnalyzer();
});

// Add some additional styles for the modal content
const additionalStyles = `
    <style>
        .detailed-results .section {
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .detailed-results .section:last-child {
            border-bottom: none;
        }
        
        .detailed-results h4 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        
        .summary-grid, .detail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .summary-item, .detail-grid > div {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #e9ecef;
        }
        
        .risk-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .risk-badge.high {
            background: #ff6b6b;
            color: white;
        }
        
        .risk-badge.medium {
            background: #ffd93d;
            color: #333;
        }
        
        .risk-badge.low {
            background: #51cf66;
            color: white;
        }
        
        .risk-factors, .recommendations-list {
            list-style: none;
            padding: 0;
        }
        
        .risk-factors li, .recommendations-list li {
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .risk-factors li:before {
            content: "⚠️";
        }
        
        .recommendations-list li:before {
            content: "💡";
        }
        
        .transcript {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e9ecef;
            max-height: 200px;
            overflow-y: auto;
            font-family: monospace;
            line-height: 1.5;
        }
    </style>
`;

document.head.insertAdjacentHTML('beforeend', additionalStyles); 