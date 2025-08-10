import { AudioChunk, EarlyRiskScore, BackendMessage, FrontendMessage, SessionData } from './types';
import { getConfig } from './config';

declare const chrome: any;

export class CommunicationService {
  private websocket: WebSocket | null = null;
  private sessionId: string | null = null;
  private isConnected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor() {
    this.sessionId = this.generateSessionId();
  }

  private generateSessionId(): string {
    return `ext_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  async connect(): Promise<void> {
    try {
      const config = await getConfig();
      const wsUrl = config.websocketUrl.replace('ws://', 'ws://').replace('https://', 'wss://');
      
      this.websocket = new WebSocket(wsUrl);
      
      this.websocket.onopen = () => {
        console.log('WebSocket connected to backend');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        
        // Send session start message
        this.sendMessage({
          type: 'session_start',
          sessionId: this.sessionId!,
          data: {
            startTime: Date.now(),
            userAgent: navigator.userAgent,
            extensionVersion: '1.0.0'
          },
          timestamp: Date.now()
        });
      };

      this.websocket.onmessage = (event) => {
        try {
          const message: FrontendMessage = JSON.parse(event.data);
          this.handleIncomingMessage(message);
        } catch (error) {
          console.error('Failed to parse incoming message:', error);
        }
      };

      this.websocket.onclose = () => {
        console.log('WebSocket disconnected');
        this.isConnected = false;
        this.attemptReconnect();
      };

      this.websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnected = false;
      };

    } catch (error) {
      console.error('Failed to connect to backend:', error);
      throw error;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  private handleIncomingMessage(message: FrontendMessage): void {
    switch (message.type) {
      case 'risk_alert':
        this.handleRiskAlert(message);
        break;
      case 'session_update':
        this.handleSessionUpdate(message);
        break;
      case 'full_report_ready':
        this.handleFullReportReady(message);
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  }

  private handleRiskAlert(message: FrontendMessage): void {
    // Send message to popup/content script
    chrome.runtime.sendMessage({
      type: 'risk_alert',
      data: message.data
    }).catch(() => {
      // Popup might not be open, that's okay
    });
  }

  private handleSessionUpdate(message: FrontendMessage): void {
    // Send session update to popup
    chrome.runtime.sendMessage({
      type: 'session_update',
      data: message.data
    }).catch(() => {
      // Popup might not be open, that's okay
    });
  }

  private handleFullReportReady(message: FrontendMessage): void {
    // Notify that full report is ready
    chrome.runtime.sendMessage({
      type: 'full_report_ready',
      data: message.data
    }).catch(() => {
      // Popup might not be open, that's okay
    });
  }

  async sendAudioChunk(audioChunk: AudioChunk): Promise<void> {
    if (!this.isConnected || !this.websocket) {
      throw new Error('Not connected to backend');
    }

    const message: BackendMessage = {
      type: 'audio_chunk',
      sessionId: this.sessionId!,
      data: audioChunk,
      timestamp: Date.now()
    };

    this.sendMessage(message);
  }

  async sendRiskScore(riskScore: EarlyRiskScore): Promise<void> {
    if (!this.isConnected || !this.websocket) {
      throw new Error('Not connected to backend');
    }

    const message: BackendMessage = {
      type: 'risk_score',
      sessionId: this.sessionId!,
      data: riskScore,
      timestamp: Date.now()
    };

    this.sendMessage(message);
  }

  private sendMessage(message: BackendMessage): void {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not ready, message not sent:', message.type);
    }
  }

  async sendSessionEnd(): Promise<void> {
    if (this.isConnected && this.websocket) {
      const message: BackendMessage = {
        type: 'session_end',
        sessionId: this.sessionId!,
        data: {
          endTime: Date.now(),
          duration: Date.now() - (this.sessionId ? parseInt(this.sessionId.split('_')[1]) : Date.now())
        },
        timestamp: Date.now()
      };

      this.sendMessage(message);
    }
  }

  disconnect(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.isConnected = false;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  isBackendConnected(): boolean {
    return this.isConnected;
  }

  // HTTP API methods for fallback
  async sendAudioChunkHTTP(audioChunk: AudioChunk): Promise<void> {
    try {
      const config = await getConfig();
      const response = await fetch(`${config.backendUrl}/api/audio_chunk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sessionId: this.sessionId,
          audioChunk: audioChunk
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to send audio chunk via HTTP:', error);
      throw error;
    }
  }

  async sendRiskScoreHTTP(riskScore: EarlyRiskScore): Promise<void> {
    try {
      const config = await getConfig();
      const response = await fetch(`${config.backendUrl}/api/risk_score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sessionId: this.sessionId,
          riskScore: riskScore
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to send risk score via HTTP:', error);
      throw error;
    }
  }
} 