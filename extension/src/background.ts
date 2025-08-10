import { SimpleAudioProcessor } from './audioProcessor';
import { CommunicationService } from './communicationService';
import { AudioChunk, EarlyRiskScore, EarlyRiskFeatures, ExtensionConfig } from './types';
import { getConfig, saveConfig } from './config';

declare const chrome: any;

class CallGuardBackground {
  private audioProcessor: SimpleAudioProcessor;
  private communicationService: CommunicationService;
  private isActive = false;
  private chunkInterval: number | null = null;
  private currentSession: any = null;

  constructor() {
    this.audioProcessor = new SimpleAudioProcessor();
    this.communicationService = new CommunicationService();
    this.initializeMessageHandlers();
  }

  private initializeMessageHandlers(): void {
    chrome.runtime.onMessage.addListener((message: any, sender: any, sendResponse: (response: any) => void) => {
      this.handleMessage(message, sender, sendResponse);
      return true; // Keep message channel open for async response
    });

    // Handle extension installation
    chrome.runtime.onInstalled.addListener(() => {
      console.log('CallGuard extension installed');
      this.initializeExtension();
    });

    // Handle extension startup
    chrome.runtime.onStartup.addListener(() => {
      console.log('CallGuard extension started');
      this.initializeExtension();
    });
  }

  private async initializeExtension(): Promise<void> {
    try {
      const config = await getConfig();
      if (config.enabled) {
        await this.startProtection();
      }
    } catch (error) {
      console.error('Failed to initialize extension:', error);
    }
  }

  private async handleMessage(message: any, sender: any, sendResponse: (response: any) => void): Promise<void> {
    try {
      switch (message.type) {
        case 'start_protection':
          await this.startProtection();
          sendResponse({ success: true, sessionId: this.communicationService.getSessionId() });
          break;

        case 'stop_protection':
          await this.stopProtection();
          sendResponse({ success: true });
          break;

        case 'get_status':
          const status = await this.getStatus();
          sendResponse(status);
          break;

        case 'update_config':
          await this.updateConfig(message.config);
          sendResponse({ success: true });
          break;

        case 'test_connection':
          const connectionStatus = await this.testBackendConnection();
          sendResponse(connectionStatus);
          break;

        case 'content_message':
          await this.handleContentMessage(message.data);
          sendResponse({ success: true });
          break;

        case 'content_script_loaded':
          console.log('Content script loaded on:', message.url);
          sendResponse({ success: true });
          break;

        default:
          sendResponse({ error: 'Unknown message type' });
      }
    } catch (error: any) {
      console.error('Error handling message:', error);
      sendResponse({ error: error.message });
    }
  }

  private async startProtection(): Promise<void> {
    if (this.isActive) {
      console.log('Protection already active');
      return;
    }

    try {
      console.log('Starting CallGuard protection...');

      // Connect to backend
      await this.communicationService.connect();

      // Start voice intensity monitoring
      this.audioProcessor.startVoiceIntensityMonitoring((intensity) => {
        console.log('Voice intensity:', intensity);
      });
      
      // Start audio recording
      await this.audioProcessor.startRecording();

      // No chunk interval needed with real-time analysis
      console.log('Real-time analysis started - no chunk processing needed');

      this.isActive = true;
      this.currentSession = {
        startTime: Date.now(),
        sessionId: this.communicationService.getSessionId()
      };

      console.log('CallGuard protection started successfully');
      
      // Notify popup of status change
      this.notifyStatusChange();

    } catch (error) {
      console.error('Failed to start protection:', error);
      throw error;
    }
  }

  private async stopProtection(): Promise<void> {
    if (!this.isActive) {
      console.log('Protection not active');
      return;
    }

    try {
      console.log('Stopping CallGuard protection...');

      // No chunk interval to clear with real-time analysis

      // Stop voice intensity monitoring
      this.audioProcessor.stopRecording();

      // End session with backend
      await this.communicationService.sendSessionEnd();
      this.communicationService.disconnect();

      this.isActive = false;
      this.currentSession = null;

      console.log('CallGuard protection stopped successfully');
      
      // Notify popup of status change
      this.notifyStatusChange();

    } catch (error) {
      console.error('Failed to stop protection:', error);
      throw error;
    }
  }

  private async processAudioChunk(): Promise<void> {
    try {
      // With the new real-time API, this method is no longer needed
      // Real-time analysis is handled by the startRealTimeAnalysis callback
      // This method is kept for compatibility but does nothing
      console.log('Real-time analysis active - no chunk processing needed');
      
    } catch (error) {
      console.error('Error in processAudioChunk:', error);
    }
  }

  private async getRiskLevel(score: number): Promise<'low' | 'medium' | 'high'> {
    const config = await getConfig();
    if (score >= config.riskThresholds.high) return 'high';
    if (score >= config.riskThresholds.medium) return 'medium';
    return 'low';
  }

  private async checkRiskThresholds(riskScore: EarlyRiskScore): Promise<void> {
    const config = await getConfig();
    
    if (riskScore.score >= config.riskThresholds.high) {
      this.showHighRiskAlert(riskScore);
    } else if (riskScore.score >= config.riskThresholds.medium) {
      this.showMediumRiskAlert(riskScore);
    }
  }

  private showHighRiskAlert(riskScore: EarlyRiskScore): void {
    // Show high risk notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: '🚨 High Risk Call Detected',
      message: `Risk Score: ${riskScore.score}/100 - ${riskScore.features.keywords.join(', ')}`,
      priority: 2
    });

    // Send alert to popup
    chrome.runtime.sendMessage({
      type: 'risk_alert',
      level: 'high',
      data: riskScore
    }).catch(() => {
      // Popup might not be open
    });
  }

  private showMediumRiskAlert(riskScore: EarlyRiskScore): void {
    // Send alert to popup
    chrome.runtime.sendMessage({
      type: 'risk_alert',
      level: 'medium',
      data: riskScore
    }).catch(() => {
      // Popup might not be open
    });
  }

  private async getStatus(): Promise<any> {
    const config = await getConfig();
    return {
      isActive: this.isActive,
      isBackendConnected: this.communicationService.isBackendConnected(),
      sessionId: this.communicationService.getSessionId(),
      currentSession: this.currentSession,
      config: {
        enabled: config.enabled,
        chunkDuration: config.chunkDuration,
        riskThresholds: config.riskThresholds
      }
    };
  }

  private async updateConfig(newConfig: any): Promise<void> {
    // Update configuration
    const currentConfig = await getConfig();
    const updatedConfig = { ...currentConfig, ...newConfig };
    await saveConfig(updatedConfig);
  }

  private async testBackendConnection(): Promise<any> {
    try {
      await this.communicationService.connect();
      const isConnected = this.communicationService.isBackendConnected();
      this.communicationService.disconnect();
      
      return {
        success: true,
        connected: isConnected
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  private notifyStatusChange(): void {
    chrome.runtime.sendMessage({
      type: 'status_changed',
      data: {
        isActive: this.isActive,
        sessionId: this.communicationService.getSessionId()
      }
    }).catch(() => {
      // Popup might not be open
    });
  }

  private async handleContentMessage(contentMessage: any): Promise<void> {
    try {
      switch (contentMessage.type) {
        case 'CALLGUARD_GET_STATUS':
          // Send protection status to content script
          await this.sendMessageToContentScript({
            type: 'CALLGUARD_RESPONSE_STATUS',
            data: await this.getStatus()
          });
          break;

        case 'CALLGUARD_REPORT_ACTIVITY':
          // Handle suspicious activity reported from webpage
          console.log('Suspicious activity reported:', contentMessage.data);
          
          // If protection is active, this could trigger additional analysis
          if (this.isActive) {
            // Log the activity for backend analysis
            await this.communicationService.sendRiskScore({
              score: 50, // Medium risk for suspicious webpage activity
              level: 'medium',
              features: {
                keywords: ['suspicious_webpage_activity'],
                language: 'en',
                languageConfidence: 1.0,
                speakingRate: 0,
                pitchVariance: 0,
                stressLevel: 0,
                syntheticVoiceLikelihood: 0
              },
              timestamp: Date.now(),
              sessionId: this.communicationService.getSessionId() || 'unknown'
            });
          }
          break;

        default:
          console.log('Unknown content message type:', contentMessage.type);
      }
    } catch (error) {
      console.error('Error handling content message:', error);
    }
  }

  private async sendMessageToContentScript(message: any): Promise<void> {
    try {
      // Send message to all active tabs
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      
      for (const tab of tabs) {
        if (tab.id) {
          await chrome.tabs.sendMessage(tab.id, message);
        }
      }
    } catch (error) {
      console.error('Failed to send message to content script:', error);
    }
  }
}

// Initialize the background service
const callGuard = new CallGuardBackground();

// Export for testing purposes
export { CallGuardBackground }; 