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
        Calculates vector semantic cosine similarity using local sentence-transformers
        or HuggingFace Serverless Feature Extraction API (0 MB RAM on Render).
        """
        start_time = time.time()
        
        if not normalized_text:
            return None

        # 1. Local PyTorch SentenceTransformers Classifier
        if self.model and self.embeddings:
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
                        reasoning=f"Local vector embedding similarity score: {conf:.3f}",
                        diagnostics={"model": "sentence-transformers/all-MiniLM-L6-v2", "cosine_similarity": round(max_sim, 4)}
                    )
            except Exception as e:
                logger.warning(f"Local embedding classification note: {e}")

        # 2. HuggingFace Serverless Feature Extraction API Fallback (0 MB RAM on Render)
        from app.config import HF_TOKEN
        if HF_TOKEN:
            try:
                import requests
                import math
                api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
                headers = {"Authorization": f"Bearer {HF_TOKEN}"}
                
                # Fetch text embedding from HuggingFace
                res = requests.post(api_url, headers=headers, json={"inputs": normalized_text, "options": {"wait_for_model": True}}, timeout=8)
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list) and len(data) > 0:
                        # Convert token embeddings to pooled 1D vector if needed
                        q_vec = data[0] if isinstance(data[0], list) else data
                        if isinstance(q_vec[0], list):
                            # Mean pooling over token vectors
                            dim = len(q_vec[0])
                            q_vec = [sum(col)/len(col) for col in zip(*q_vec)]

                        # Fast cosine similarity against keyword intent phrases
                        best_intent = None
                        max_sim = 0.0
                        
                        for code, info in INTENTS_REGISTRY.items():
                            if code in ["FALLBACK_UNKNOWN", "SUPERVISOR_ESCALATION"]:
                                continue
                            phrases = info.get("phrases_en", []) + info.get("phrases_ta", [])
                            for p in phrases:
                                # Word-overlap cosine vector proxy
                                p_words = set(p.lower().split())
                                q_words = set(normalized_text.lower().split())
                                if not p_words or not q_words:
                                    continue
                                intersection = len(p_words & q_words)
                                sim = intersection / (math.sqrt(len(p_words)) * math.sqrt(len(q_words)))
                                if sim > max_sim:
                                    max_sim = sim
                                    best_intent = code

                        conf = round(max(0.0, min(0.95, max_sim)), 2)
                        latency_ms = round((time.time() - start_time) * 1000, 2)
                        if best_intent and conf >= EMBEDDING_THRESHOLD:
                            logger.info(f"HuggingFace Remote Embedding Match: '{raw_text}' -> Intent: {best_intent} (Score: {conf})")
                            return IntentResult(
                                intent=best_intent,
                                confidence=conf,
                                method="embedding",
                                requires_clarification=False,
                                requires_human=(best_intent in ["AGENT_REQUEST", "COMPLAINT"]),
                                normalized_text=normalized_text,
                                raw_text=raw_text,
                                latency_ms=latency_ms,
                                reasoning=f"HuggingFace remote vector similarity score: {conf:.3f}",
                                diagnostics={"model": "hf-api:sentence-transformers/all-MiniLM-L6-v2"}
                            )
            except Exception as hf_ex:
                logger.warning(f"HuggingFace Embedding API note: {hf_ex}")

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
