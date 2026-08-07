import re
import difflib
import logging
from functools import lru_cache
from typing import Tuple, Dict, Any, List
from app.config import INTENTS_REGISTRY

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1024)
def tokenize_cached(text: str) -> Tuple[str, ...]:
    """Tokenizes string with in-memory LRU caching for 0ms lookup latency."""
    return tuple([w for w in re.findall(r'[\w\u0B80-\u0BFF]+', text.lower()) if len(w) > 1])

def calculate_similarity(query_text: str, target_phrase: str) -> float:
    """Calculates hybrid fuzzy phrase similarity with fast token matching."""
    q_clean = query_text.lower().strip()
    p_clean = target_phrase.lower().strip()
    
    # 1. Exact or substring match (Fast path - sub-millisecond)
    if p_clean in q_clean:
        return 0.95
    if q_clean in p_clean:
        return 0.88

    # 2. Token overlap ratio (Jaccard similarity)
    q_tokens = set(tokenize_cached(q_clean))
    p_tokens = set(tokenize_cached(p_clean))

    if not q_tokens or not p_tokens:
        return 0.0

    intersection = q_tokens.intersection(p_tokens)
    union = q_tokens.union(p_tokens)
    jaccard = len(intersection) / len(union) if union else 0.0

    # 3. Sub-string token matching (for Tamil agglutinative suffixes)
    sub_matches = 0
    for qt in q_tokens:
        for pt in p_tokens:
            if len(pt) >= 3 and (pt in qt or qt in pt):
                sub_matches += 1
                break
    sub_ratio = sub_matches / max(len(p_tokens), 1)

    # 4. SequenceMatcher fuzzy similarity
    seq_ratio = difflib.SequenceMatcher(None, q_clean, p_clean).ratio()

    # Weighted blend
    score = (jaccard * 0.45) + (sub_ratio * 0.35) + (seq_ratio * 0.20)
    return round(score, 3)

class IntentClassifier:
    def __init__(self):
        self.registry = INTENTS_REGISTRY

    def classify(self, text: str, detected_lang: str = "ta") -> Tuple[str, str, float]:
        """
        Classifies query text using ultra-fast in-memory fuzzy token similarity engine.
        Returns: (intent_code, language_code, confidence_score)
        """
        clean_text = text.lower().strip()
        if not clean_text or len(clean_text) < 2:
            return "SUPERVISOR_ESCALATION", detected_lang, 0.40

        best_intent = "SUPERVISOR_ESCALATION"
        max_score = 0.0

        for intent_code, data in self.registry.items():
            if intent_code in ["FALLBACK_UNKNOWN", "SUPERVISOR_ESCALATION"]:
                continue

            phrases_en = data.get("phrases_en", [])
            phrases_ta = data.get("phrases_ta", [])
            
            primary_phrases = phrases_ta if detected_lang == "ta" else phrases_en
            secondary_phrases = phrases_en if detected_lang == "ta" else phrases_ta

            intent_max_score = 0.0
            
            for phrase in primary_phrases:
                sim = calculate_similarity(clean_text, phrase)
                if sim > intent_max_score:
                    intent_max_score = sim

            for phrase in secondary_phrases:
                sim = calculate_similarity(clean_text, phrase) * 0.9
                if sim > intent_max_score:
                    intent_max_score = sim

            # Penalize GREETING if query contains specific question topic words
            question_topics = [
                "வரி", "80g", "80c", "பணம்", "நன்கொடை", "செலுத்துவது", "ஜிபே", "upi", "குழந்தை", "முகவரி",
                "பார்க்க", "போன்", "விவரம்", "பற்றி", "பத்தி", "எப்படி", "எது", "நம்பர்", "பாலிசி", "பிரீமியம்",
                "தவணை", "லிங்க்", "இஎம்ஐ", "அட்ரஸ்", "புகார்", "ஏஜென்ட்", "ஆளு"
            ]
            if any(qt in clean_text for qt in question_topics) and intent_code == "GREETING":
                intent_max_score *= 0.1

            if intent_max_score > max_score:
                max_score = intent_max_score
                best_intent = intent_code

        # Threshold check: requires similarity score >= 0.40 to classify intent
        if max_score >= 0.40 and best_intent not in ["FALLBACK_UNKNOWN", "SUPERVISOR_ESCALATION"]:
            confidence = min(0.98, max(0.65, round(0.60 + (max_score * 0.40), 2)))
        else:
            best_intent = "FALLBACK_UNKNOWN"
            confidence = 0.42

        logger.info(f"Classified: '{text}' -> Intent: {best_intent} (Score: {max_score}, Conf: {confidence})")
        return best_intent, detected_lang, confidence

