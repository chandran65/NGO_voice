import time
import logging
from typing import Optional, Dict, Any
from app.config import INTENTS_REGISTRY, EMBEDDING_THRESHOLD
from app.canonical_intent import IntentResult

logger = logging.getLogger(__name__)

# Global Singleton Model & Embeddings Cache
_MODEL_INSTANCE = None
_INTENT_EMBEDDINGS_CACHE = {}
_LOGGED_MISSING_MODULE = False

def get_embedding_model():
    """Returns singleton SentenceTransformer instance cached across process lifetime."""
    global _MODEL_INSTANCE, _LOGGED_MISSING_MODULE
    if _MODEL_INSTANCE is None and not _LOGGED_MISSING_MODULE:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading Singleton SentenceTransformer ('sentence-transformers/all-MiniLM-L6-v2')...")
            _MODEL_INSTANCE = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            logger.info("SentenceTransformer model loaded successfully.")
        except ImportError:
            _LOGGED_MISSING_MODULE = True
            logger.info("SentenceTransformers not installed (RAM optimization mode enabled). Using high-precision Rule Engine.")
        except Exception as e:
            _LOGGED_MISSING_MODULE = True
            logger.info(f"SentenceTransformers note: {e}. Using high-precision Rule Engine.")
            _MODEL_INSTANCE = None
    return _MODEL_INSTANCE

def get_intent_embeddings():
    """Returns pre-computed intent category embeddings cached across process lifetime."""
    global _INTENT_EMBEDDINGS_CACHE
    if not _INTENT_EMBEDDINGS_CACHE:
        model = get_embedding_model()
        if model is not None:
            try:
                for code, data in INTENTS_REGISTRY.items():
                    if code in ["FALLBACK_UNKNOWN", "SUPERVISOR_ESCALATION"]:
                        continue
                    phrases = data.get("phrases_en", []) + data.get("phrases_ta", [])
                    descriptions = [data.get("description_en", ""), data.get("description_ta", "")]
                    all_targets = [p for p in (phrases + descriptions) if p and len(p.strip()) > 1]
                    if all_targets:
                        _INTENT_EMBEDDINGS_CACHE[code] = model.encode(all_targets, convert_to_tensor=True)
                logger.info(f"Pre-computed embeddings for {len(_INTENT_EMBEDDINGS_CACHE)} intent categories.")
            except Exception as ex:
                logger.error(f"Error pre-computing intent embeddings: {ex}")
    return _INTENT_EMBEDDINGS_CACHE

class EmbeddingClassifier:
    def __init__(self):
        # Warmup singleton model & embeddings cache on initialization
        self.model = get_embedding_model()
        self.embeddings = get_intent_embeddings()

    def classify(self, normalized_text: str, raw_text: str) -> Optional[IntentResult]:
        """
        Calculates vector semantic cosine similarity using sentence-transformers.
        Returns IntentResult if best similarity >= EMBEDDING_THRESHOLD, otherwise None.
        """
        start_time = time.time()
        
        if not self.model or not self.embeddings or not normalized_text:
            return None

        try:
            from sentence_transformers import util
            q_emb = self.model.encode(normalized_text, convert_to_tensor=True)

            best_intent = None
            max_sim = 0.0

            for intent_code, phrase_embs in self.embeddings.items():
                sims = util.cos_sim(q_emb, phrase_embs)
                intent_max = sims.max().item()
                if intent_max > max_sim:
                    max_sim = intent_max
                    best_intent = intent_code

            # Calibrate confidence score
            conf = round(max(0.0, min(0.95, max_sim)), 2)
            latency_ms = round((time.time() - start_time) * 1000, 2)

            if best_intent and conf >= EMBEDDING_THRESHOLD:
                requires_human = (best_intent in ["AGENT_REQUEST", "COMPLAINT"])
                logger.info(f"Embedding Classifier Match: '{raw_text}' -> Intent: {best_intent} (Score: {conf}, Latency: {latency_ms}ms)")
                
                return IntentResult(
                    intent=best_intent,
                    confidence=conf,
                    method="embedding",
                    requires_clarification=False,
                    requires_human=requires_human,
                    normalized_text=normalized_text,
                    raw_text=raw_text,
                    latency_ms=latency_ms,
                    reasoning=f"Vector embedding cosine similarity score: {conf:.3f}",
                    diagnostics={
                        "model": "sentence-transformers/all-MiniLM-L6-v2",
                        "cosine_similarity": round(max_sim, 4),
                        "threshold": EMBEDDING_THRESHOLD
                    }
                )
        except Exception as e:
            logger.warning(f"Embedding classification exception: {e}")

        return None
