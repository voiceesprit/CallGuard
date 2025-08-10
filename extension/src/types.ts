export interface AudioChunk {
  id: string;
  timestamp: number;
  data: Float32Array;
  sampleRate: number;
  duration: number;
}

export interface EarlyRiskFeatures {
  keywords: string[];
  language: string;
  languageConfidence: number;
  speakingRate: number;
  pitchVariance: number;
  stressLevel: number;
  syntheticVoiceLikelihood: number;
}

export interface EarlyRiskScore {
  score: number; // 0-100
  level: 'low' | 'medium' | 'high';
  features: EarlyRiskFeatures;
  timestamp: number;
  sessionId: string;
}

export interface ScamKeyword {
  phrase: string;
  language: string;
  weight: number;
  category: string;
}

export interface ExtensionConfig {
  enabled: boolean;
  chunkDuration: number; // seconds
  riskThresholds: {
    low: number;
    medium: number;
    high: number;
  };
  keywords: ScamKeyword[];
  backendUrl: string;
  websocketUrl: string;
}

export interface SessionData {
  sessionId: string;
  startTime: number;
  audioChunks: AudioChunk[];
  riskScores: EarlyRiskScore[];
  status: 'active' | 'paused' | 'ended';
}

export interface BackendMessage {
  type: 'audio_chunk' | 'risk_score' | 'session_start' | 'session_end';
  sessionId: string;
  data: AudioChunk | EarlyRiskScore | any;
  timestamp: number;
}

export interface FrontendMessage {
  type: 'risk_alert' | 'session_update' | 'full_report_ready';
  sessionId: string;
  data: any;
  timestamp: number;
}

// Enhanced types for real-time analysis and persuasion detection
export interface PersuasionCues {
  detected: boolean;
  urgency: boolean;
  authority: boolean;
  socialProof: boolean;
  reciprocity: boolean;
  commitment: boolean;
  liking: boolean;
  confidence: number;
  timestamp: number;
  details?: {
    keywords: string[];
    phrases: string[];
    emotionalPressure: number;
    speechPatterns: string[];
  };
}

export interface CallContext {
  platform: string;
  confidence: number;
  participants: number;
  timestamp: number;
  sessionId?: string;
  duration?: number;
}

export interface RealTimeAudioFeatures {
  spectralCentroid: number;
  spectralRolloff: number;
  spectralFlux: number;
  rms: number;
  zeroCrossingRate: number;
  energy: number;
  timestamp: number;
}

export interface CulturalProfile {
  directness: 'low' | 'medium' | 'high';
  urgencyThreshold: 'very_low' | 'low' | 'medium' | 'high' | 'very_high';
  authorityRespect: 'low' | 'medium' | 'high' | 'very_high';
  socialProofWeight: 'low' | 'medium' | 'high' | 'very_high';
  reciprocityStyle: 'explicit' | 'implicit';
}

export interface FullAnalysisResult {
  sessionId: string;
  timestamp: number;
  duration: number;
  riskScore: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  persuasionAnalysis: {
    detectedPrinciples: string[];
    confidence: number;
    culturalContext: string;
    recommendations: string[];
  };
  audioAnalysis: {
    speakingRate: number;
    pitchVariance: number;
    stressLevel: number;
    syntheticVoiceLikelihood: number;
    emotionalPressure: number;
  };
  transcript: {
    text: string;
    language: string;
    confidence: number;
    timestamps: Array<{ start: number; end: number; text: string }>;
  };
  alerts: Array<{
    type: 'persuasion' | 'urgency' | 'authority' | 'synthetic_voice';
    severity: 'low' | 'medium' | 'high';
    message: string;
    timestamp: number;
    context: string;
  }>;
}

export interface RealTimeAlert {
  id: string;
  type: 'persuasion' | 'risk' | 'call_detected';
  severity: 'low' | 'medium' | 'high';
  message: string;
  timestamp: number;
  details: any;
  actionRequired: boolean;
}

export interface CallSession {
  id: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  platform: string;
  participants: number;
  riskHistory: Array<{
    timestamp: number;
    riskScore: number;
    persuasionCues: PersuasionCues;
  }>;
  alerts: RealTimeAlert[];
  status: 'active' | 'paused' | 'ended' | 'analyzing';
} 