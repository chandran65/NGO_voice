import time
import logging
from typing import Optional
from app.config import INTENTS_REGISTRY, RULE_THRESHOLD
from app.canonical_intent import IntentResult

logger = logging.getLogger(__name__)

# High-priority explicit trigger patterns for deterministic rule engine
EXPLICIT_RULE_PATTERNS = {
    "AGENT_REQUEST": [
        "speak to human officer", "human officer", "talk to human agent", "connect to representative",
        "speak to manager", "human support", "ngo officer", "how do i trust you", "how can i trust",
        "is this genuine", "is this real", "real or fake", "how do i know",
        "மனித அதிகாரியிடம் பேச வேண்டும்", "அதிகாரியிடம் பேச வேண்டும்", "மனித அதிகாரி", "ஹியூமன் ஆபிசர்",
        "அதிகாரி கூட பேசணும்", "அதிகாரி கிட்ட பேசுறேன்", "ஏஜென்ட் கிட்ட மாத்துங்க", "ஆளு கிட்ட பேசணும்",
        "எப்படி உங்களை நம்புவது", "நான் எப்படி உங்களை நம்புவது", "எப்படி நம்புறது", "உங்களை எப்படி நம்பறது",
        "எப்படி நம்புறது உங்களை", "நிஜமா பேசுறீங்களா"
    ],
    "COMPLAINT": [
        "complaint", "wrong service", "fraud", "scam", "bad experience", "grievance",
        "புகார்", "தவறான சேவை", "மோசமான சர்வீஸ்", "கேம்பளைண்ட்", "பணம் பிடிச்சுட்டாங்க",
        "பிரச்சனை", "ஏமாத்துறீங்களா", "புகார் பதிவு பண்ணுங்க"
    ],
    "PAYMENT_LINK": [
        "gpay link", "upi link", "payment link", "send upi link", "send payment link",
        "ஜிபே லிங்க்", "ஜிபி லிங்க்", "பேமெண்ட் லிங்க்", "லிங்க் அனுப்புங்க", "ஆன்லைன்ல செலுத்தணும்",
        "எஸ்எம்எஸ் லிங்க் அனுப்புங்க", "வாட்ஸ்அப் லிங்க்", "பேமெண்ட் எப்படி பண்றது"
    ],
    "TAX_BENEFITS": [
        "80g", "80g certificate", "tax exemption", "income tax benefit", "tax rebate",
        "80g வருமான வரி விலக்கு", "வரி விலக்கு சான்றிதழ்", "வரி விலக்கு", "80ஜி", "இன்கம் டாக்ஸ்"
    ],
    "DONATION_USAGE": [
        "donation utilization", "where does money go", "how funds spent", "how is donation used",
        "பணம் எப்படி பயன்படும்", "எதுக்கு செலவு", "நன்கொடை செலவு", "பயன்பாடு", "பணம் என்ன ஆகும்",
        "எதுக்காக யூஸ் ஆகுது", "நன்கொடை எதுக்காக யூஸ் ஆகுது", "எதுக்கு யூஸ் ஆகுது", "யூஸ் ஆகுது"
    ],
    "SPONSOR_CHILD": [
        "sponsor child", "adopt child", "child education support", "child sponsor",
        "குழந்தை ஸ்பான்சர்", "குழந்தை தத்தெடுப்பு", "ஒரு குழந்தையை படிக்க வைக்க", "குழந்தை படிப்பு"
    ],
    "ADDRESS_UPDATE": [
        "change address", "update address", "wrong address", "new address",
        "முகவரி மாற்ற வேண்டும்", "அட்ரஸ் மாத்தணும்", "போன் நம்பர் மாத்தணும்", "அட்ரஸ் சேஞ்ச்", "முகவரி திருத்தம்"
    ],
    "CALLBACK_REQUEST": [
        "call me later", "call back", "busy right now", "call tomorrow",
        "அப்புறம் கூப்பிடுங்க", "இப்போ பிஸியா இருக்கேன்", "நாளைக்கு கால் பண்ணுங்க", "சாயங்காலம் கூப்பிடுங்க", "கால் பேக் பண்ணுங்க",
        "நான் இப்ப பிசியா இருக்கேன் அப்புறம் கால் பண்ணுங்க", "பிசியா இருக்கேன் அப்புறம் கால் பண்ணுங்க", "இப்ப பிஸியா இருக்கேன்",
        "அப்புறம் கால் பண்ணுங்க", "பிஸியா இருக்கேன்"
    ],
    "RECEIPT_REQUEST": [
        "donation receipt", "get receipt", "official receipt", "invoice",
        "ரசீது தருவீங்களா", "நன்கொடை ரசீது", "பில் சான்று", "ரசீது எப்போ வரும்", "ரசீது பெற"
    ],
    "NUMBER_SOURCE": [
        "where did you get my number", "who gave my contact", "how you got my phone",
        "என் போன் நம்பர் எப்படி உங்களுக்கு கிடைச்சது", "என் நம்பர் எப்படி கிடைச்சுச்சு", "யாரு என் நம்பர் கொடுத்தா"
    ],
    "ABOUT_HOME": [
        "about foundation", "tell me about children home", "where is home located",
        "அறக்கட்டளை பற்றி சொல்லுங்க", "குழந்தைகள் இல்லம் எங்கே உள்ளது", "இல்லம் பற்றி", "ஹோம் பத்தி சொல்லுங்க"
    ],
    "GREETING": [
        "hello", "hi", "hey", "good morning", "good afternoon", "vanakkam",
        "வணக்கம்", "வணக்கம் சார்", "வணக்கம் மேடம்", "ஹலோ சார்", "காலை வணக்கம்"
    ]
}

class RuleClassifier:
    def classify(self, normalized_text: str, raw_text: str) -> Optional[IntentResult]:
        """
        Executes high-precision deterministic rule matching.
        Returns IntentResult if confidence >= RULE_THRESHOLD, otherwise None.
        """
        start_time = time.time()
        text_lower = normalized_text.lower().strip()
        raw_lower = raw_text.lower().strip()

        if not text_lower:
            return None

        best_intent = None
        best_confidence = 0.0
        reason = None

        # Check explicit high-priority rule patterns
        for intent_code, phrases in EXPLICIT_RULE_PATTERNS.items():
            for phrase in phrases:
                phrase_lower = phrase.lower().strip()
                # Exact match or strong phrase boundary match
                if phrase_lower == text_lower or phrase_lower == raw_lower:
                    best_intent = intent_code
                    best_confidence = 0.95
                    reason = f"Exact rule match for phrase '{phrase}'"
                    break
                elif phrase_lower in text_lower or phrase_lower in raw_lower:
                    # Substring match confidence calibrated by coverage
                    coverage = len(phrase_lower) / max(len(text_lower), 1)
                    conf = round(min(0.92, max(0.85, 0.85 + (coverage * 0.07))), 2)
                    if conf > best_confidence:
                        best_confidence = conf
                        best_intent = intent_code
                        reason = f"Deterministic substring rule match for '{phrase}'"

            if best_confidence >= 0.95:
                break

        # Check if score meets configured RULE_THRESHOLD
        if best_intent and best_confidence >= RULE_THRESHOLD:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            requires_human = (best_intent in ["AGENT_REQUEST", "COMPLAINT"])
            
            logger.info(f"Rule Classifier Match: '{raw_text}' -> Intent: {best_intent} (Conf: {best_confidence}, Latency: {latency_ms}ms)")
            
            return IntentResult(
                intent=best_intent,
                confidence=best_confidence,
                method="rule",
                requires_clarification=False,
                requires_human=requires_human,
                normalized_text=normalized_text,
                raw_text=raw_text,
                latency_ms=latency_ms,
                reasoning=reason,
                diagnostics={
                    "rule_engine": "deterministic_keyword_matcher",
                    "phrase_match": reason,
                    "confidence_calibrated": True
                }
            )

        return None
