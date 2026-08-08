import time
import logging
from typing import Tuple, Dict, Any, Optional

from app.config import (
    RULE_THRESHOLD,
    EMBEDDING_THRESHOLD,
    LLM_THRESHOLD,
    MAX_CLARIFICATION_ATTEMPTS
)
from app.canonical_intent import IntentResult
from app.services.normalizer import TextNormalizer
from app.services.rule_classifier import RuleClassifier
from app.services.embedding_classifier import EmbeddingClassifier
from app.services.llm_classifier import LLMClassifier

logger = logging.getLogger(__name__)

class LayeredIntentResolver:
    """
    5-Stage Layered Intent Resolution Pipeline:
    Transcript → Normalization → Rule Classifier → Embedding Classifier → LLM Classifier → Clarification → Human Escalation
    """
    def __init__(self):
        self.normalizer = TextNormalizer()
        self.rule_classifier = RuleClassifier()
        self.embedding_classifier = EmbeddingClassifier()
        self.llm_classifier = LLMClassifier()

    def resolve(self, raw_text: str, language: str = "ta") -> IntentResult:
        """
        Processes transcript through the layered pipeline and returns a canonical IntentResult.
        """
        start_time = time.time()
        
        # Step 1: Language normalization
        norm_text = self.normalizer.normalize(raw_text, language=language)

        if not norm_text or len(norm_text) < 2:
            return IntentResult(
                intent="FALLBACK_UNKNOWN",
                confidence=0.40,
                method="fallback",
                requires_clarification=True,
                requires_human=False,
                normalized_text=norm_text,
                raw_text=raw_text,
                latency_ms=round((time.time() - start_time) * 1000, 2),
                reasoning="Empty or trivial transcript after normalization",
                diagnostics={"accepted": False, "fallback_reason": "empty_input"}
            )

        # Step 2: Deterministic Rule Classifier
        rule_res = self.rule_classifier.classify(norm_text, raw_text)
        if rule_res and rule_res.confidence >= RULE_THRESHOLD:
            rule_res.diagnostics["accepted"] = True
            rule_res.diagnostics["total_pipeline_latency_ms"] = round((time.time() - start_time) * 1000, 2)
            self._log_observability(rule_res)
            return rule_res

        # Step 3: Vector Embedding Classifier
        emb_res = self.embedding_classifier.classify(norm_text, raw_text)
        if emb_res and emb_res.confidence >= EMBEDDING_THRESHOLD:
            emb_res.diagnostics["accepted"] = True
            emb_res.diagnostics["total_pipeline_latency_ms"] = round((time.time() - start_time) * 1000, 2)
            self._log_observability(emb_res)
            return emb_res

        # Step 4: Structured LLM Classifier Fallback
        llm_res = self.llm_classifier.classify(norm_text, raw_text)
        if llm_res and llm_res.confidence >= LLM_THRESHOLD:
            llm_res.diagnostics["accepted"] = True
            llm_res.diagnostics["total_pipeline_latency_ms"] = round((time.time() - start_time) * 1000, 2)
            self._log_observability(llm_res)
            return llm_res

        # Step 5: Clarification / Inconclusive Fallback
        total_latency = round((time.time() - start_time) * 1000, 2)
        fallback_res = IntentResult(
            intent="FALLBACK_UNKNOWN",
            confidence=0.42,
            method="clarification",
            requires_clarification=True,
            requires_human=False,
            normalized_text=norm_text,
            raw_text=raw_text,
            latency_ms=total_latency,
            reasoning="All layered classifiers (Rule, Embedding, LLM) were inconclusive below thresholds",
            diagnostics={
                "accepted": False,
                "score": 0.42,
                "classifier": "clarification_fallback",
                "fallback_reason": "below_all_thresholds",
                "latency_ms": total_latency,
                "rule_attempted": bool(rule_res),
                "embedding_attempted": bool(emb_res),
                "llm_attempted": bool(llm_res)
            }
        )
        self._log_observability(fallback_res)
        return fallback_res

    def _log_observability(self, result: IntentResult):
        """Records structured diagnostic observability telemetry log for every classification attempt."""
        telemetry = {
            "classifier": result.method,
            "intent": result.intent,
            "score": result.confidence,
            "accepted": result.diagnostics.get("accepted", False),
            "latency_ms": result.latency_ms,
            "fallback_reason": result.diagnostics.get("fallback_reason", "none")
        }
        logger.info(f"INSPECT_TELEMETRY: {telemetry}")
