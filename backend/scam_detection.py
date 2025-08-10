import re
from typing import Tuple
import torch
import joblib
import numpy as np

from transformers import pipeline, GPT2LMHeadModel, GPT2Tokenizer
from sentence_transformers import SentenceTransformer

# --------- Text Preprocessing ---------

FILLER_WORDS = {
    "en": ["um", "uh", "er", "ah", "like", "you know"],
    "fr": ["euh", "bah", "ben", "hein"],
    "es": ["eh", "este", "pues", "o sea"],
}

try:
    import langid
except ImportError:
    langid = None  # optional

def clean_text(
    text: str,
    lang_hint: str = "auto",
) -> Tuple[str, str, bool]:
    original_text = text.lower()
    normalized_text = re.sub(r"\s+", " ", original_text).strip()

    lang_code = lang_hint
    if lang_hint == "auto":
        if langid:
            lang_code, _ = langid.classify(normalized_text)
        else:
            lang_code = "en"

    fillers = FILLER_WORDS.get(lang_code, [])

    has_filler = False
    if fillers:
        filler_pattern = r"(?:\b)(" + "|".join(map(re.escape, fillers)) + r")(?:\b|(?=\W))"
        if re.search(filler_pattern, normalized_text):
            has_filler = True
        cleaned_text = re.sub(filler_pattern, "", normalized_text)
        cleaned_text = re.sub(r"[,\.\!\?]+(?=\s|$)", "", cleaned_text)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
    else:
        cleaned_text = normalized_text

    return cleaned_text, lang_code, has_filler

# --------- Scam Detection ---------

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def predict_scam(text):
    labels = ["scam", "legitimate"]
    result = classifier(text, candidate_labels=labels)
    scam_score = next(score for label, score in zip(result['labels'], result['scores']) if label == "scam")
    return scam_score

def rule_based_score(text):
    keywords = {
        "gift card": 0.4,
        "bitcoin": 0.7,
        "wire transfer": 0.7,
        "password": 0.5,
        "immediately": 0.5,
        "arrest": 0.6,
        "verify": 0.5,
        "urgent": 0.5,
        "transfer now": 0.6,
        "call immediately": 0.6,
        "account suspended": 0.6,
        "password reset": 0.5,
        "remote access": 0.6,
        "wire money": 0.7,
        "back taxes": 0.7,
        "compromised": 0.6,
        "unauthorized": 0.6,
        "disconnected": 0.5,
        "legal action": 0.7,
        "warrant": 0.7,
        "social security": 0.6,
        "install": 0.5,
        "prize": 0.4,
        "pay immediately": 0.6,
        "pay your bill now": 0.7,
        "confirm your details": 0.6,
        "avoid legal consequences": 0.7,
    }
    score = 0
    text_lower = text.lower()
    for kw, weight in keywords.items():
        if kw in text_lower:
            score += weight
    return min(score, 1.0)

def combined_scam_score(text):
    zero_shot = predict_scam(text)
    rule_score = rule_based_score(text)
    combined = 0.4 * zero_shot + 0.6 * rule_score
    return combined

# --------- Logistic Regression Scam Prediction ---------

# Load models ONCE globally (make sure files are present in your working dir)
sentence_transformer_model_name = open("sentence_transformer_model.txt").read().strip()
embedding_model = SentenceTransformer(sentence_transformer_model_name)
logistic_model = joblib.load("final_logistic_regression.joblib")

def logistic_predict(texts):
    embeddings = embedding_model.encode(texts)
    probs = logistic_model.predict_proba(embeddings)[:, 1]
    return probs

# --------- Bot/Human Detection via GPT-2 Perplexity ---------

gpt2_tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
gpt2_model = GPT2LMHeadModel.from_pretrained("gpt2")

def perplexity(text):
    inputs = gpt2_tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        outputs = gpt2_model(**inputs, labels=inputs["input_ids"])
        loss = outputs.loss
    return torch.exp(loss).item()

def bot_human_label(ppl, threshold=20):
    return "BOT-like" if ppl < threshold else "HUMAN-like"

# --------- Final Detection Function ---------

def detect_scam_and_bot(text, scam_threshold=0.4, ppl_threshold=20):
    cleaned_text, lang, has_filler = clean_text(text)
    scam_rule_score = combined_scam_score(cleaned_text)
    logistic_score = logistic_predict([cleaned_text])[0]
    ppl = perplexity(text)
    bot_label = bot_human_label(ppl, threshold=ppl_threshold)
    combined_scam = 0.5 * scam_rule_score + 0.5 * logistic_score
    is_scam = combined_scam > scam_threshold

    return {
        "scam": "YES" if is_scam else "NO",
        "bot_or_human": bot_label,
        "combined_scam_score": combined_scam,
        "perplexity": ppl,
        "lang": lang,
        "has_filler": has_filler,
    }

# --------- Example usage ---------

if __name__ == "__main__":
    samples = [
        "Your account has been compromised. Send your password immediately.",
        "Hello, this is a friendly reminder about your upcoming appointment.",
        "Transfer money to the provided Bitcoin wallet to avoid legal consequences."
    ]

    for text in samples:
        result = detect_scam_and_bot(text)
        print(f"Text: {text}")
        print(f"Scam: {result['scam']}")
        print(f"Bot/Human: {result['bot_or_human']}")
        print(f"Combined Scam Score: {result['combined_scam_score']:.4f}")
        print(f"Perplexity: {result['perplexity']:.2f}")
        print(f"Language: {result['lang']}")
        print(f"Filler Words Detected: {result['has_filler']}")
        print("-" * 40)
