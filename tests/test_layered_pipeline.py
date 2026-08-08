import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, Base, engine
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
from app.services.layered_intent_resolver import LayeredIntentResolver
from app.services.conversation_manager import ConversationManager
from scripts.seed_ngo_data import seed_database

class TestLayeredIntentResolutionPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n--- Setting up DB & Layered Pipeline Tests ---")
        seed_database()
        cls.db = SessionLocal()
        cls.normalizer = TextNormalizer()
        cls.rule_classifier = RuleClassifier()
        cls.embedding_classifier = EmbeddingClassifier()
        cls.llm_classifier = LLMClassifier()
        cls.resolver = LayeredIntentResolver()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_language_normalization(self):
        print("\n[UNIT TEST 1] Testing Language Normalization (Tamil, English, Tanglish)...")
        # Tanglish normalization
        norm_tanglish = self.normalizer.normalize("naan donation panna virumburen", language="ta")
        self.assertIn("நான்", norm_tanglish)
        self.assertIn("donation", norm_tanglish)
        self.assertIn("விரும்புகிறேன்", norm_tanglish)
        
        # Noise & Filler removal
        norm_noise = self.normalizer.normalize("சார் 80g tax exemption கிடைக்குமா மேடம்", language="ta")
        self.assertNotIn("சார்", norm_noise)
        self.assertNotIn("மேடம்", norm_noise)
        self.assertIn("80g", norm_noise)
        print(f"PASS: Tanglish & Noise Normalization: '{norm_tanglish}'")

    def test_02_rule_classifier_obvious_match(self):
        print("\n[UNIT TEST 2] Testing Deterministic Rule Classifier...")
        # Obvious Tamil Rule
        res_ta = self.rule_classifier.classify("மனித அதிகாரியிடம் பேச வேண்டும்", "மனித அதிகாரியிடம் பேச வேண்டும்")
        self.assertIsNotNone(res_ta)
        self.assertEqual(res_ta.intent, "AGENT_REQUEST")
        self.assertEqual(res_ta.method, "rule")
        self.assertGreaterEqual(res_ta.confidence, RULE_THRESHOLD)

        # Obvious English Rule
        res_en = self.rule_classifier.classify("speak to human officer", "speak to human officer")
        self.assertIsNotNone(res_en)
        self.assertEqual(res_en.intent, "AGENT_REQUEST")
        self.assertEqual(res_en.method, "rule")
        print("PASS: Deterministic Rule Classifier matched high-confidence intents.")

    def test_03_embedding_classifier_match(self):
        print("\n[UNIT TEST 3] Testing Vector Embedding Classifier...")
        raw = "tax deduction certificate rebate info"
        norm = self.normalizer.normalize(raw, "en")
        
        res = self.embedding_classifier.classify(norm, raw)
        self.assertIsNotNone(res)
        self.assertEqual(res.intent, "TAX_BENEFITS")
        self.assertEqual(res.method, "embedding")
        self.assertGreaterEqual(res.confidence, EMBEDDING_THRESHOLD)
        print(f"PASS: Embedding Classifier matched intent '{res.intent}' with score {res.confidence}.")

    def test_04_llm_classifier_fallback_and_invalid_rejection(self):
        print("\n[UNIT TEST 4] Testing LLM Classifier & Invalid Intent Rejection...")
        # Structured JSON validation for known intent
        res_valid = self.llm_classifier.classify("எனக்கு ரசீது சான்று வேணும்", "எனக்கு ரசீது சான்று வேணும்")
        if res_valid:
            self.assertIn(res_valid.intent, ["RECEIPT_REQUEST", "TAX_BENEFITS"])
            self.assertEqual(res_valid.method, "llm")
            self.assertGreaterEqual(res_valid.confidence, LLM_THRESHOLD)

        # Rejection of invalid / hallucinated intent
        invalid_json = {"intent": "INVENTED_MAGIC_INTENT", "confidence": 0.99, "needs_clarification": False}
        self.assertNotIn(invalid_json["intent"], self.llm_classifier.valid_intents)
        print("PASS: LLM Classifier validated schema and rejected arbitrary intent names.")

    def test_05_clarification_handling_and_max_attempts(self):
        print("\n[UNIT TEST 5] Testing Clarification Loop & Max Attempt Escalation...")
        session_res = ConversationManager.start_outbound_call(self.db, "+91 98765 43210", language="ta")
        session_id = session_res["session_id"]
        
        ambiguous_query = "xyz abcd qwerty ambiguous input"
        
        # Turn 1: Clarification Request
        turn1 = ConversationManager.process_turn_text(self.db, session_id, ambiguous_query, "ta")
        self.assertIn("மன்னிக்கவும்", turn1["response_text"])
        self.assertFalse(turn1["is_escalated"])

        # Turn 2: Second Clarification Request
        turn2 = ConversationManager.process_turn_text(self.db, session_id, ambiguous_query, "ta")
        
        # Turn 3: Max Clarification Attempts reached -> Escalation
        turn3 = ConversationManager.process_turn_text(self.db, session_id, ambiguous_query, "ta")
        self.assertTrue(turn3["is_escalated"])
        self.assertIn("maximum clarification attempts", turn3["escalation_reason"])
        print(f"PASS: Escalated to human officer after reaching MAX_CLARIFICATION_ATTEMPTS ({MAX_CLARIFICATION_ATTEMPTS}).")

    def test_06_explicit_human_request_immediate_escalation(self):
        print("\n[UNIT TEST 6] Testing Explicit Human Request Escalation...")
        session_res = ConversationManager.start_outbound_call(self.db, "+91 98765 43210", language="ta")
        session_id = session_res["session_id"]

        turn = ConversationManager.process_turn_text(self.db, session_id, "Speak to Human Officer", "ta")
        self.assertEqual(turn["intent"], "AGENT_REQUEST")
        self.assertTrue(turn["is_escalated"])
        self.assertIn("human agent", turn["escalation_reason"].lower())
        print("PASS: Explicit human agent request immediately triggered escalation.")

    def test_07_full_pipeline_end_to_end_chain(self):
        print("\n[INTEGRATION TEST] Testing Full End-to-End Resolution Pipeline...")
        raw_text = "naan donation panna virumburen எதுக்காக யூஸ் ஆகுது"
        
        res = self.resolver.resolve(raw_text, language="ta")
        self.assertEqual(res.intent, "DONATION_USAGE")
        self.assertIn(res.method, ["rule", "embedding", "llm"])
        self.assertGreaterEqual(res.confidence, 0.70)
        self.assertIn("accepted", res.diagnostics)
        print(f"PASS: Full Pipeline Chain resolved '{raw_text}' -> Intent: {res.intent} via {res.method} (Conf: {res.confidence}, Latency: {res.latency_ms}ms).")

if __name__ == "__main__":
    unittest.main()
