import { ExtensionConfig, ScamKeyword } from './types';

declare const chrome: any;

export const DEFAULT_CONFIG: ExtensionConfig = {
  enabled: false,
  chunkDuration: 3, // 3 seconds
  riskThresholds: {
    low: 30,
    medium: 60,
    high: 80
  },
  keywords: [
    // English scam keywords
    { phrase: "your account has been compromised", language: "en", weight: 0.9, category: "account_security" },
    { phrase: "social security number", language: "en", weight: 0.8, category: "identity_theft" },
    { phrase: "tax debt", language: "en", weight: 0.7, category: "tax_scam" },
    { phrase: "gift cards", language: "en", weight: 0.8, category: "payment_scam" },
    { phrase: "bitcoin payment", language: "en", weight: 0.9, category: "crypto_scam" },
    { phrase: "urgent action required", language: "en", weight: 0.6, category: "urgency" },
    { phrase: "government agency", language: "en", weight: 0.7, category: "authority" },
    { phrase: "bank account frozen", language: "en", weight: 0.9, category: "financial" },
    { phrase: "inheritance", language: "en", weight: 0.6, category: "inheritance_scam" },
    { phrase: "lottery winner", language: "en", weight: 0.8, category: "lottery_scam" },
    
    // Spanish scam keywords
    { phrase: "su cuenta ha sido comprometida", language: "es", weight: 0.9, category: "account_security" },
    { phrase: "número de seguro social", language: "es", weight: 0.8, category: "identity_theft" },
    { phrase: "deuda fiscal", language: "es", weight: 0.7, category: "tax_scam" },
    { phrase: "tarjetas de regalo", language: "es", weight: 0.8, category: "payment_scam" },
    { phrase: "pago bitcoin", language: "es", weight: 0.9, category: "crypto_scam" },
    
    // French scam keywords
    { phrase: "votre compte a été compromis", language: "fr", weight: 0.9, category: "account_security" },
    { phrase: "numéro de sécurité sociale", language: "fr", weight: 0.8, category: "identity_theft" },
    { phrase: "dette fiscale", language: "fr", weight: 0.7, category: "tax_scam" },
    
    // German scam keywords
    { phrase: "ihr konto wurde kompromittiert", language: "de", weight: 0.9, category: "account_security" },
    { phrase: "sozialversicherungsnummer", language: "de", weight: 0.8, category: "identity_theft" },
    { phrase: "steuerschulden", language: "de", weight: 0.7, category: "tax_scam" },
    
    // Chinese scam keywords
    { phrase: "您的账户已被盗用", language: "zh", weight: 0.9, category: "account_security" },
    { phrase: "社会安全号码", language: "zh", weight: 0.8, category: "identity_theft" },
    { phrase: "税务债务", language: "zh", weight: 0.7, category: "tax_scam" }
  ],
  backendUrl: "http://localhost:5000",
  websocketUrl: "ws://localhost:5000/ws"
};

export const getConfig = async (): Promise<ExtensionConfig> => {
  try {
    const stored = await (chrome as any).storage.sync.get('config');
    return { ...DEFAULT_CONFIG, ...stored.config };
  } catch {
    return DEFAULT_CONFIG;
  }
};

export const saveConfig = async (config: ExtensionConfig): Promise<void> => {
  await (chrome as any).storage.sync.set({ config });
};

export const getKeywordsForLanguage = (language: string): ScamKeyword[] => {
  return DEFAULT_CONFIG.keywords.filter(k => k.language === language);
}; 