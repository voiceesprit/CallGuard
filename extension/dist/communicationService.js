"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CommunicationService = void 0;
const config_1 = require("./config");
class CommunicationService {
    constructor() {
        this.websocket = null;
        this.sessionId = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.sessionId = this.generateSessionId();
    }
    generateSessionId() {
        return `ext_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    async connect() {
        try {
            const config = await (0, config_1.getConfig)();
            const wsUrl = config.websocketUrl.replace('ws://', 'ws://').replace('https://', 'wss://');
            this.websocket = new WebSocket(wsUrl);
            this.websocket.onopen = () => {
                console.log('WebSocket connected to backend');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                // Send session start message
                this.sendMessage({
                    type: 'session_start',
                    sessionId: this.sessionId,
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
                    const message = JSON.parse(event.data);
                    this.handleIncomingMessage(message);
                }
                catch (error) {
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
        }
        catch (error) {
            console.error('Failed to connect to backend:', error);
            throw error;
        }
    }
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        }
        else {
            console.error('Max reconnection attempts reached');
        }
    }
    handleIncomingMessage(message) {
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
    handleRiskAlert(message) {
        // Send message to popup/content script
        chrome.runtime.sendMessage({
            type: 'risk_alert',
            data: message.data
        }).catch(() => {
            // Popup might not be open, that's okay
        });
    }
    handleSessionUpdate(message) {
        // Send session update to popup
        chrome.runtime.sendMessage({
            type: 'session_update',
            data: message.data
        }).catch(() => {
            // Popup might not be open, that's okay
        });
    }
    handleFullReportReady(message) {
        // Notify that full report is ready
        chrome.runtime.sendMessage({
            type: 'full_report_ready',
            data: message.data
        }).catch(() => {
            // Popup might not be open, that's okay
        });
    }
    async sendAudioChunk(audioChunk) {
        if (!this.isConnected || !this.websocket) {
            throw new Error('Not connected to backend');
        }
        const message = {
            type: 'audio_chunk',
            sessionId: this.sessionId,
            data: audioChunk,
            timestamp: Date.now()
        };
        this.sendMessage(message);
    }
    async sendRiskScore(riskScore) {
        if (!this.isConnected || !this.websocket) {
            throw new Error('Not connected to backend');
        }
        const message = {
            type: 'risk_score',
            sessionId: this.sessionId,
            data: riskScore,
            timestamp: Date.now()
        };
        this.sendMessage(message);
    }
    sendMessage(message) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        }
        else {
            console.warn('WebSocket not ready, message not sent:', message.type);
        }
    }
    async sendSessionEnd() {
        if (this.isConnected && this.websocket) {
            const message = {
                type: 'session_end',
                sessionId: this.sessionId,
                data: {
                    endTime: Date.now(),
                    duration: Date.now() - (this.sessionId ? parseInt(this.sessionId.split('_')[1]) : Date.now())
                },
                timestamp: Date.now()
            };
            this.sendMessage(message);
        }
    }
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.isConnected = false;
    }
    getSessionId() {
        return this.sessionId;
    }
    isBackendConnected() {
        return this.isConnected;
    }
    // HTTP API methods for fallback
    async sendAudioChunkHTTP(audioChunk) {
        try {
            const config = await (0, config_1.getConfig)();
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
        }
        catch (error) {
            console.error('Failed to send audio chunk via HTTP:', error);
            throw error;
        }
    }
    async sendRiskScoreHTTP(riskScore) {
        try {
            const config = await (0, config_1.getConfig)();
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
        }
        catch (error) {
            console.error('Failed to send risk score via HTTP:', error);
            throw error;
        }
    }
}
exports.CommunicationService = CommunicationService;
