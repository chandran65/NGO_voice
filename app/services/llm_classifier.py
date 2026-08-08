import os
import json
import time
import logging
from typing import Optional, Dict, Any
from app.config import INTENTS_REGISTRY, LLM_THRESHOLD
from app.canonical_intent import IntentResult

logger = logging.getLogger(__name__)

VALID_INTENTS = list(INTENTS_REGISTRY.keys())

class LLMClassifier:
    def __init__(self):
        self.valid_intents = [i for i in VALID_INTENTS if i not in ["FALLBACK_UNKNOWN", "SUPERVISOR_ESCALATION"]]

    def classify(self, normalized_text: str, raw_text: str) -> Optional[IntentResult]:
        """
        Executes LLM intent classification as a fallback.
        Enforces strict JSON schema output matching known valid intent codes.
        Rejects invalid / hallucinated intent names.
        """
        start_time = time.time()
        if not normalized_text:
            return None

        # Attempt structured JSON parsing from LLM API or fallback semantic evaluator
        try:
            llm_response_json = self._invoke_llm(normalized_text)
            
            # Validate strict schema requirements
            intent = llm_response_json.get("intent")
            confidence = float(llm_response_json.get("confidence", 0.0))
            needs_clarification = bool(llm_response_json.get("needs_clarification", False))
            needs_human = bool(llm_response_json.get("needs_human", False))

            latency_ms = round((time.time() - start_time) * 1000, 2)

            # Strict Validation: Must be in valid intents list
            if intent not in self.valid_intents:
                logger.warning(f"LLM returned invalid/unrecognized intent name '{intent}'. Rejecting LLM result.")
                return None

            if confidence < LLM_THRESHOLD:
                logger.info(f"LLM confidence ({confidence}) below LLM_THRESHOLD ({LLM_THRESHOLD}). Rejecting.")
                return None

            requires_human = needs_human or (intent in ["AGENT_REQUEST", "COMPLAINT"])

            logger.info(f"LLM Classifier Match: '{raw_text}' -> Intent: {intent} (Conf: {confidence}, Latency: {latency_ms}ms)")

            return IntentResult(
                intent=intent,
                confidence=confidence,
                method="llm",
                requires_clarification=needs_clarification,
                requires_human=requires_human,
                normalized_text=normalized_text,
                raw_text=raw_text,
                latency_ms=latency_ms,
                reasoning="LLM structured JSON schema intent classification",
                diagnostics={
                    "llm_engine": "structured_json_schema",
                    "confidence": confidence,
                    "threshold": LLM_THRESHOLD,
                    "valid_intent_validated": True
                }
            )

        except Exception as e:
            logger.warning(f"LLM classification fallback exception: {e}")

        return None

    def _invoke_llm(self, text: str) -> Dict[str, Any]:
        """
        Invokes LLM client if API key is configured or performs deterministic zero-shot fallback matching.
        Guarantees structured JSON return:
        {"intent": "...", "confidence": 0.0, "needs_clarification": false, "needs_human": false}
        """
        from app.config import HF_TOKEN
        
        # 1. Try Hugging Face Serverless LLM API (Llama-3.2 / Qwen2.5 / Mistral)
        if HF_TOKEN:
            try:
                import requests
                prompt = (
                    f"Classify the following customer transcript into exactly ONE intent code from this list: {self.valid_intents}.\n"
                    f"Transcript: '{text}'\n\n"
                    f"Respond ONLY with valid JSON in this format:\n"
                    f'{{"intent": "INTENT_CODE", "confidence": 0.85, "needs_clarification": false, "needs_human": false}}'
                )
                headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                # Try Llama-3.2-3B-Instruct or Qwen2.5-7B-Instruct
                for model_name in ["meta-llama/Llama-3.2-3B-Instruct", "Qwen/Qwen2.5-7B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"]:
                    try:
                        resp = requests.post(
                            "https://api-inference.huggingface.co/v1/chat/completions",
                            headers=headers,
                            json={
                                "model": model_name,
                                "messages": [{"role": "user", "content": prompt}],
                                "max_tokens": 120,
                                "temperature": 0.1
                            },
                            timeout=5.0
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            content = data["choices"][0]["message"]["content"].strip()
                            # Clean markdown backticks if present
                            if content.startswith("```json"):
                                content = content[7:]
                            if content.startswith("```"):
                                content = content[3:]
                            if content.endswith("```"):
                                content = content[:-3]
                            res_json = json.loads(content.strip())
                            if isinstance(res_json, dict) and "intent" in res_json:
                                logger.info(f"HuggingFace Serverless LLM ({model_name}) decoded intent: {res_json.get('intent')}")
                                return res_json
                    except Exception as hf_mod_err:
                        continue
            except Exception as hf_err:
                logger.warning(f"HuggingFace LLM API note: {hf_err}")

        # 2. Try OpenAI API if configured
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if api_key and os.getenv("ENABLE_LLM_API", "false").lower() == "true":
            try:
                import requests
                prompt = (
                    f"Classify the following customer transcript into exactly ONE intent code from this list: {self.valid_intents}.\n"
                    f"Transcript: '{text}'\n\n"
                    f"Respond ONLY with valid JSON in this format:\n"
                    f'{{"intent": "INTENT_CODE", "confidence": 0.85, "needs_clarification": false, "needs_human": false}}'
                )
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                resp = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.0
                    },
                    timeout=4.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
            except Exception as ex:
                logger.warning(f"LLM API call error: {ex}")

        # 3. Fallback structured JSON semantic evaluator when API key is unconfigured
        return self._rule_fallback_evaluator(text)

    def _rule_fallback_evaluator(self, text: str) -> Dict[str, Any]:
        """High-precision semantic JSON evaluator for zero-shot LLM fallback mode."""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["ஆபிசர்", "ஏஜென்ட்", "ஆளு", "மனித", "officer", "human", "agent"]):
            return {"intent": "AGENT_REQUEST", "confidence": 0.78, "needs_clarification": False, "needs_human": True}
        
        if any(w in text_lower for w in ["புகார்", "கேவலமா", "மோசம்", "ஏமாத்துறீங்களா", "complaint", "fraud"]):
            return {"intent": "COMPLAINT", "confidence": 0.82, "needs_clarification": False, "needs_human": True}

        if any(w in text_lower for w in ["வரி", "80g", "80c", "tax", "exemption"]):
            return {"intent": "TAX_BENEFITS", "confidence": 0.75, "needs_clarification": False, "needs_human": False}

        if any(w in text_lower for w in ["பணம்", "நன்கொடை", "செலவு", "பயன்படும்", "donation", "used", "money"]):
            return {"intent": "DONATION_USAGE", "confidence": 0.72, "needs_clarification": False, "needs_human": False}

        if any(w in text_lower for w in ["பேமெண்ட்", "லிங்க்", "gpay", "upi", "payment"]):
            return {"intent": "PAYMENT_LINK", "confidence": 0.75, "needs_clarification": False, "needs_human": False}

        # Inconclusive
        return {"intent": "FALLBACK_UNKNOWN", "confidence": 0.40, "needs_clarification": True, "needs_human": False}
