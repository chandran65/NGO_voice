import logging
from typing import Tuple, Dict, Any
from app.services.layered_intent_resolver import LayeredIntentResolver

logger = logging.getLogger(__name__)

# Global Singleton Layered Intent Resolver Instance
_RESOLVER_INSTANCE = None

def get_layered_resolver() -> LayeredIntentResolver:
    global _RESOLVER_INSTANCE
    if _RESOLVER_INSTANCE is None:
        _RESOLVER_INSTANCE = LayeredIntentResolver()
    return _RESOLVER_INSTANCE

class IntentClassifier:
    """
    Facade wrapping LayeredIntentResolver for 100% backward compatibility with public services & API.
    """
    def __init__(self):
        self.resolver = get_layered_resolver()

    def classify(self, text: str, detected_lang: str = "ta") -> Tuple[str, str, float]:
        """
        Classifies transcript using the 5-Stage Layered Intent Resolution System.
        Returns: (intent_code, language_code, confidence_score)
        """
        res = self.resolver.resolve(text, language=detected_lang)
        return res.intent, detected_lang, res.confidence

    def predict(self, text: str, language: str = "ta") -> Dict[str, Any]:
        """
        Convenience method returning dict with canonical intent result details.
        """
        res = self.resolver.resolve(text, language=language)
        return {
            "intent": res.intent,
            "language": language,
            "confidence": res.confidence,
            "method": res.method,
            "requires_clarification": res.requires_clarification,
            "requires_human": res.requires_human,
            "normalized_text": res.normalized_text,
            "latency_ms": res.latency_ms
        }
