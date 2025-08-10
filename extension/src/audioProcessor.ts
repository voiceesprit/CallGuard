import { AudioChunk, EarlyRiskFeatures, PersuasionCues, CallContext } from './types';

export class SimpleAudioProcessor {
  private mediaRecorder: MediaRecorder | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private microphone: MediaStreamAudioSourceNode | null = null;
  private isRecording = false;
  private voiceIntensityCallback: ((intensity: number) => void) | null = null;
  private intensityInterval: number | null = null;

  constructor() {}

  // Simple audio recording
  async startRecording(): Promise<MediaRecorder> {
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

      const chunks: Blob[] = [];
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        await this.sendAudioToBackend(audioBlob);
      };

      // Start recording
      this.mediaRecorder.start();
      this.isRecording = true;

      return this.mediaRecorder;
    } catch (error) {
      console.error('Failed to start recording:', error);
      throw error;
    }
  }

  // Stop recording
  stopRecording(): void {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
    this.isRecording = false;
    }
    
    // Stop voice intensity monitoring
    if (this.intensityInterval) {
      clearInterval(this.intensityInterval);
      this.intensityInterval = null;
    }
  }

  // Start real-time voice intensity monitoring
  startVoiceIntensityMonitoring(callback: (intensity: number) => void): void {
    this.voiceIntensityCallback = callback;
    
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      this.audioContext = new AudioContext();
      this.microphone = this.audioContext.createMediaStreamSource(stream);
      this.analyser = this.audioContext.createAnalyser();
      
      this.microphone.connect(this.analyser);
      
      // Monitor voice intensity every 100ms
      this.intensityInterval = window.setInterval(() => {
        if (this.analyser && this.voiceIntensityCallback) {
          const intensity = this.getVoiceIntensity();
          this.voiceIntensityCallback(intensity);
        }
      }, 100);
    });
  }

  // Get current voice intensity (0-100)
  private getVoiceIntensity(): number {
    if (!this.analyser) return 0;
    
    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    this.analyser.getByteFrequencyData(dataArray);
    
    // Calculate RMS (Root Mean Square) for intensity
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i] * dataArray[i];
    }
    const rms = Math.sqrt(sum / bufferLength);
    
    // Convert to 0-100 scale
    return Math.min(100, Math.max(0, (rms / 255) * 100));
  }

  // Send audio to backend for analysis
  private async sendAudioToBackend(audioBlob: Blob): Promise<void> {
    try {
      // Convert to WAV format
      const wavBlob = await this.convertToWAV(audioBlob);
      
      // Create FormData for upload
      const formData = new FormData();
      formData.append('audio', wavBlob, 'recording.wav');
      formData.append('sessionId', this.getSessionId());
      
      // Send to backend
      const response = await fetch('http://localhost:5000/analyze-audio', {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const report = await response.json();
        console.log('Analysis report received:', report);
        
        // You can emit this report to the popup or store it
        this.emitAnalysisReport(report);
      } else {
        console.error('Backend analysis failed:', response.statusText);
      }
      
    } catch (error) {
      console.error('Failed to send audio to backend:', error);
    }
  }

  // Convert WebM to WAV format
  private async convertToWAV(webmBlob: Blob): Promise<Blob> {
    const audioContext = new AudioContext();
    const arrayBuffer = await webmBlob.arrayBuffer();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    
    // Convert to WAV format
    const wavBuffer = this.audioBufferToWav(audioBuffer);
    return new Blob([wavBuffer], { type: 'audio/wav' });
  }

  // Convert AudioBuffer to WAV format
  private audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
    const length = buffer.length;
    const numberOfChannels = buffer.numberOfChannels;
    const sampleRate = buffer.sampleRate;
    const arrayBuffer = new ArrayBuffer(44 + length * numberOfChannels * 2);
    const view = new DataView(arrayBuffer);
    
    // WAV header
    const writeString = (offset: number, string: string) => {
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

  // Generate session ID
  private getSessionId(): string {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Emit analysis report (you can customize this)
  private emitAnalysisReport(report: any): void {
    // Dispatch custom event that popup can listen to
    const event = new CustomEvent('analysisReport', { detail: report });
    window.dispatchEvent(event);
  }
}

// Export alias for backward compatibility
export const AudioProcessor = SimpleAudioProcessor; 