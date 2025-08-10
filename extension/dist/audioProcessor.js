"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AudioProcessor = exports.EnhancedAudioProcessor = void 0;
class EnhancedAudioProcessor {
    constructor() {
        this.mediaRecorder = null;
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.isRecording = false;
        this.callDetectionActive = false;
        this.lastFrequencyData = null;
        this.persuasionDetector = new RealTimePersuasionDetector();
        this.culturalProfiles = new CulturalPersuasionProfiles();
    }
    // Enhanced call detection
    async detectActiveCall() {
        try {
            // Check for common call platforms
            const callPlatforms = this.detectCallPlatforms();
            if (callPlatforms.length > 0) {
                // Analyze audio to confirm call activity
                const audioContext = new AudioContext();
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const source = audioContext.createMediaStreamSource(stream);
                const analyser = audioContext.createAnalyser();
                source.connect(analyser);
                // Detect call characteristics (multiple speakers, consistent audio levels)
                const callCharacteristics = await this.analyzeCallCharacteristics(analyser);
                if (callCharacteristics.isCall) {
                    return {
                        platform: callPlatforms[0],
                        confidence: callCharacteristics.confidence,
                        participants: callCharacteristics.participantCount,
                        timestamp: Date.now()
                    };
                }
            }
            return null;
        }
        catch (error) {
            console.error('Call detection failed:', error);
            return null;
        }
    }
    detectCallPlatforms() {
        const platforms = [];
        const url = window.location.href;
        const userAgent = navigator.userAgent;
        if (url.includes('zoom.us') || userAgent.includes('Zoom'))
            platforms.push('Zoom');
        if (url.includes('teams.microsoft.com') || userAgent.includes('Teams'))
            platforms.push('Teams');
        if (url.includes('meet.google.com') || userAgent.includes('Meet'))
            platforms.push('Google Meet');
        if (url.includes('webex.com') || userAgent.includes('Webex'))
            platforms.push('Webex');
        if (url.includes('discord.com') || userAgent.includes('Discord'))
            platforms.push('Discord');
        if (url.includes('skype.com') || userAgent.includes('Skype'))
            platforms.push('Skype');
        return platforms;
    }
    async analyzeCallCharacteristics(analyser) {
        return new Promise((resolve) => {
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            let samples = 0;
            let totalEnergy = 0;
            let varianceCount = 0;
            let lastEnergy = 0;
            const sampleInterval = setInterval(() => {
                analyser.getByteFrequencyData(dataArray);
                const energy = dataArray.reduce((sum, val) => sum + val, 0);
                totalEnergy += energy;
                if (samples > 0) {
                    const variance = Math.abs(energy - lastEnergy);
                    if (variance > 100)
                        varianceCount++;
                }
                lastEnergy = energy;
                samples++;
                if (samples >= 30) { // 3 seconds of analysis
                    clearInterval(sampleInterval);
                    const avgEnergy = totalEnergy / samples;
                    const varianceRatio = varianceCount / samples;
                    // Call detection logic
                    const isCall = avgEnergy > 50 && varianceRatio > 0.3;
                    const confidence = isCall ? Math.min(0.9, 0.5 + (varianceRatio * 0.4)) : 0.1;
                    const participantCount = isCall ? Math.max(2, Math.floor(avgEnergy / 30)) : 1;
                    resolve({ isCall, confidence, participantCount });
                }
            }, 100);
        });
    }
    // Enhanced real-time audio processing with persuasion detection
    async startRealTimeAnalysis(onPersuasionDetected, onRiskUpdate) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.audioContext = new AudioContext();
            this.analyser = this.audioContext.createAnalyser();
            this.microphone = this.audioContext.createMediaStreamSource(stream);
            this.analyser.fftSize = 2048;
            this.analyser.smoothingTimeConstant = 0.8;
            this.microphone.connect(this.analyser);
            this.isRecording = true;
            // Start real-time analysis loop
            this.analyzeRealTime(onPersuasionDetected, onRiskUpdate);
        }
        catch (error) {
            console.error('Failed to start real-time analysis:', error);
            throw error;
        }
    }
    analyzeRealTime(onPersuasionDetected, onRiskUpdate) {
        if (!this.analyser || !this.isRecording)
            return;
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        const timeDataArray = new Uint8Array(bufferLength);
        const analyzeFrame = () => {
            if (!this.isRecording)
                return;
            this.analyser.getByteFrequencyData(dataArray);
            this.analyser.getByteTimeDomainData(timeDataArray);
            // Extract real-time features
            const features = this.extractRealTimeFeatures(dataArray, timeDataArray);
            // Detect persuasion cues
            const persuasionCues = this.persuasionDetector.analyzeStream(features);
            if (persuasionCues.detected) {
                onPersuasionDetected(persuasionCues);
            }
            // Calculate real-time risk score
            const riskScore = this.calculateRealTimeRisk(features, persuasionCues);
            onRiskUpdate(riskScore);
            // Continue analysis
            requestAnimationFrame(analyzeFrame);
        };
        analyzeFrame();
    }
    extractRealTimeFeatures(frequencyData, timeData) {
        // Calculate frequency domain features
        const spectralCentroid = this.calculateSpectralCentroid(frequencyData);
        const spectralRolloff = this.calculateSpectralRolloff(frequencyData);
        const spectralFlux = this.calculateSpectralFlux(frequencyData, this.lastFrequencyData);
        // Calculate time domain features
        const rms = this.calculateRMS(timeData);
        const zeroCrossingRate = this.calculateZeroCrossingRate(timeData);
        const energy = this.calculateEnergy(frequencyData);
        // Store for next frame
        this.lastFrequencyData = new Uint8Array(frequencyData);
        return {
            spectralCentroid,
            spectralRolloff,
            spectralFlux,
            rms,
            zeroCrossingRate,
            energy,
            timestamp: Date.now()
        };
    }
    // Enhanced 1-minute recording with persuasion analysis
    async startCallRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            const chunks = [];
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunks.push(event.data);
                }
            };
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(chunks, { type: 'audio/webm' });
                await this.processFullRecording(audioBlob);
            };
            // Start recording
            this.mediaRecorder.start();
            // Stop after 1 minute
            setTimeout(() => {
                if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                    this.mediaRecorder.stop();
                }
            }, 60000);
            return this.mediaRecorder;
        }
        catch (error) {
            console.error('Failed to start call recording:', error);
            throw error;
        }
    }
    async processFullRecording(audioBlob) {
        try {
            // Convert to WAV format for backend processing
            const wavBlob = await this.convertToWAV(audioBlob);
            // Send to backend for full analysis
            await this.sendFullRecording(wavBlob);
        }
        catch (error) {
            console.error('Failed to process full recording:', error);
        }
    }
    async convertToWAV(webmBlob) {
        // Convert WebM to WAV format
        const audioContext = new AudioContext();
        const arrayBuffer = await webmBlob.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        // Convert to WAV format
        const wavBuffer = this.audioBufferToWav(audioBuffer);
        return new Blob([wavBuffer], { type: 'audio/wav' });
    }
    audioBufferToWav(buffer) {
        const length = buffer.length;
        const numberOfChannels = buffer.numberOfChannels;
        const sampleRate = buffer.sampleRate;
        const arrayBuffer = new ArrayBuffer(44 + length * numberOfChannels * 2);
        const view = new DataView(arrayBuffer);
        // WAV header
        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };
        writeString(0, 'RIFF');
        view.setUint32(4, 36 + length * numberOfChannels * 2, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, numberOfChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * numberOfChannels * 2, true);
        view.setUint16(32, numberOfChannels * 2, true);
        view.setUint16(34, 16, true);
        writeString(36, 'data');
        view.setUint32(40, length * numberOfChannels * 2, true);
        // Audio data
        let offset = 44;
        for (let i = 0; i < length; i++) {
            for (let channel = 0; channel < numberOfChannels; channel++) {
                const sample = Math.max(-1, Math.min(1, buffer.getChannelData(channel)[i]));
                view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
                offset += 2;
            }
        }
        return arrayBuffer;
    }
    async sendFullRecording(wavBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', wavBlob, 'call_recording.wav');
            formData.append('timestamp', Date.now().toString());
            formData.append('sessionId', this.getSessionId());
            const response = await fetch('http://localhost:5000/api/full-analysis', {
                method: 'POST',
                body: formData
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const result = await response.json();
            console.log('Full analysis submitted:', result);
        }
        catch (error) {
            console.error('Failed to send full recording:', error);
        }
    }
    getSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    // Utility methods for feature calculation
    calculateSpectralCentroid(frequencyData) {
        let weightedSum = 0;
        let sum = 0;
        for (let i = 0; i < frequencyData.length; i++) {
            weightedSum += i * frequencyData[i];
            sum += frequencyData[i];
        }
        return sum > 0 ? weightedSum / sum : 0;
    }
    calculateSpectralRolloff(frequencyData) {
        const threshold = 0.85;
        let cumulativeSum = 0;
        const totalSum = frequencyData.reduce((sum, val) => sum + val, 0);
        for (let i = 0; i < frequencyData.length; i++) {
            cumulativeSum += frequencyData[i];
            if (cumulativeSum >= threshold * totalSum) {
                return i / frequencyData.length;
            }
        }
        return 1.0;
    }
    calculateSpectralFlux(currentData, previousData) {
        if (!previousData)
            return 0;
        let flux = 0;
        for (let i = 0; i < currentData.length; i++) {
            const diff = currentData[i] - previousData[i];
            flux += diff * diff;
        }
        return Math.sqrt(flux);
    }
    calculateRMS(timeData) {
        let sum = 0;
        for (let i = 0; i < timeData.length; i++) {
            const sample = (timeData[i] - 128) / 128;
            sum += sample * sample;
        }
        return Math.sqrt(sum / timeData.length);
    }
    calculateZeroCrossingRate(timeData) {
        let crossings = 0;
        for (let i = 1; i < timeData.length; i++) {
            const current = timeData[i] - 128;
            const previous = timeData[i - 1] - 128;
            if ((current >= 0 && previous < 0) || (current < 0 && previous >= 0)) {
                crossings++;
            }
        }
        return crossings / (timeData.length - 1);
    }
    calculateEnergy(frequencyData) {
        let energy = 0;
        for (let i = 0; i < frequencyData.length; i++) {
            energy += frequencyData[i] * frequencyData[i];
        }
        return energy / frequencyData.length;
    }
    calculateRealTimeRisk(features, persuasionCues) {
        let riskScore = 0;
        // Audio feature risk
        if (features.spectralFlux > 50)
            riskScore += 15; // High variability
        if (features.rms > 0.8)
            riskScore += 10; // Loud speech
        if (features.zeroCrossingRate > 0.3)
            riskScore += 10; // Fast speech
        // Persuasion cue risk
        if (persuasionCues.urgency)
            riskScore += 25;
        if (persuasionCues.authority)
            riskScore += 20;
        if (persuasionCues.socialProof)
            riskScore += 15;
        if (persuasionCues.reciprocity)
            riskScore += 15;
        if (persuasionCues.commitment)
            riskScore += 10;
        if (persuasionCues.liking)
            riskScore += 10;
        return Math.min(100, riskScore);
    }
    stop() {
        this.isRecording = false;
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        if (this.microphone) {
            this.microphone.disconnect();
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
    }
}
exports.EnhancedAudioProcessor = EnhancedAudioProcessor;
// Real-time persuasion detection class
class RealTimePersuasionDetector {
    constructor() {
        this.keywordPatterns = new Map();
        this.culturalContext = 'en'; // Default to English
        this.initializeKeywordPatterns();
    }
    initializeKeywordPatterns() {
        // Reciprocity patterns
        this.keywordPatterns.set('reciprocity', [
            /\b(free|gift|bonus|just for you|special offer|no cost|complimentary)\b/gi,
            /\b(help|favor|assistance|support)\b/gi
        ]);
        // Commitment & Consistency patterns
        this.keywordPatterns.set('commitment', [
            /\b(as you said|you promised|you agreed|you mentioned)\b/gi,
            /\b(we discussed|you confirmed|you understood)\b/gi
        ]);
        // Social Proof patterns
        this.keywordPatterns.set('socialProof', [
            /\b(everyone is doing|others like you|many people|thousands of|millions of)\b/gi,
            /\b(join the crowd|don't miss out|be part of|trending)\b/gi
        ]);
        // Authority patterns
        this.keywordPatterns.set('authority', [
            /\b(official|government|bank|police|IRS|tax|legal|certified)\b/gi,
            /\b(CEO|president|director|manager|supervisor)\b/gi
        ]);
        // Liking patterns
        this.keywordPatterns.set('liking', [
            /\b(you're so|you seem|you look|you sound|you appear)\b/gi,
            /\b(wonderful|amazing|fantastic|brilliant|smart)\b/gi
        ]);
        // Scarcity patterns
        this.keywordPatterns.set('scarcity', [
            /\b(only today|final chance|last opportunity|limited time|act now)\b/gi,
            /\b(expires|deadline|countdown|urgent|immediate)\b/gi
        ]);
    }
    analyzeStream(features) {
        // This would integrate with real-time speech recognition
        // For now, return based on audio features that suggest persuasion
        const cues = {
            detected: false,
            urgency: false,
            authority: false,
            socialProof: false,
            reciprocity: false,
            commitment: false,
            liking: false,
            confidence: 0,
            timestamp: Date.now()
        };
        // Detect urgency based on speech patterns
        if (features.spectralFlux > 40 && features.rms > 0.7) {
            cues.urgency = true;
            cues.detected = true;
            cues.confidence += 0.3;
        }
        // Detect authority based on speech stability
        if (features.spectralCentroid < 0.3 && features.spectralFlux < 20) {
            cues.authority = true;
            cues.detected = true;
            cues.confidence += 0.4;
        }
        // Detect social proof based on speech variability
        if (features.zeroCrossingRate > 0.25 && features.spectralRolloff > 0.7) {
            cues.socialProof = true;
            cues.detected = true;
            cues.confidence += 0.2;
        }
        return cues;
    }
    setCulturalContext(language) {
        this.culturalContext = language;
        // Adjust patterns based on cultural context
        this.adjustCulturalPatterns();
    }
    adjustCulturalPatterns() {
        // Implement cultural-specific adjustments
        // This would modify keyword patterns based on cultural context
    }
}
// Cultural persuasion profiles
class CulturalPersuasionProfiles {
    constructor() {
        this.profiles = new Map();
        this.initializeProfiles();
    }
    initializeProfiles() {
        // English (US) profile
        this.profiles.set('en', {
            directness: 'high',
            urgencyThreshold: 'medium',
            authorityRespect: 'high',
            socialProofWeight: 'medium',
            reciprocityStyle: 'explicit'
        });
        // Spanish profile
        this.profiles.set('es', {
            directness: 'medium',
            urgencyThreshold: 'low',
            authorityRespect: 'very_high',
            socialProofWeight: 'high',
            reciprocityStyle: 'implicit'
        });
        // Chinese profile
        this.profiles.set('zh', {
            directness: 'low',
            urgencyThreshold: 'very_low',
            authorityRespect: 'very_high',
            socialProofWeight: 'very_high',
            reciprocityStyle: 'implicit'
        });
    }
    getProfile(language) {
        return this.profiles.get(language) || this.profiles.get('en');
    }
}
// Export alias for backward compatibility
exports.AudioProcessor = EnhancedAudioProcessor;
