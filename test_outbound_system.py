import os
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from app.database import engine, Base, SessionLocal
from app.models import Campaign, CustomerProfile, AgentEscalation, CallSessionModel, CallTurnModel, QueryLog
from app.services.intent import IntentClassifier
from app.services.backend_api import BackendAPIService
from app.services.conversation_manager import ConversationManager
from app.services.campaign_scheduler import CampaignScheduler
from scripts.seed_ngo_data import seed_database

class TestOutboundVoiceCallingSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n--- Setting up DB for Outbound Voice Calling System Tests ---")
        seed_database()
        cls.db = SessionLocal()
        cls.classifier = IntentClassifier()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_campaign_scheduler(self):
        print("\n[TEST 1] Testing Campaign Scheduler & Customer Retrieval...")
        campaigns = CampaignScheduler.get_active_campaigns(self.db)
        self.assertGreaterEqual(len(campaigns), 1)
        self.assertEqual(campaigns[0].status, "ACTIVE")
        
        customers = CampaignScheduler.get_campaign_customers(self.db, campaigns[0].id)
        self.assertGreaterEqual(len(customers), 1)
        self.assertIn("DONOR-", customers[0].customer_id)
        print(f"PASS: Active campaign found '{campaigns[0].name}' with {len(customers)} target donors.")

    def test_02_outbound_call_start(self):
        print("\n[TEST 2] Testing Outbound Call Session Initiation...")
        res = ConversationManager.start_outbound_call(self.db, "+91 98765 43210", campaign_id=1, language="ta")
        self.assertIn("session_id", res)
        self.assertEqual(res["status"], "CONNECTED")
        self.assertIn("வணக்கம்", res["greeting_text"])
        print(f"PASS: Outbound call connected. Session ID: {res['session_id']}")

    def test_03_faq_turn(self):
        print("\n[TEST 3] Testing FAQ Query Turn (Donation Usage in Tamil)...")
        session_res = ConversationManager.start_outbound_call(self.db, "+91 98765 43210", language="ta")
        session_id = session_res["session_id"]
        
        # Customer says: "நன்கொடை பணம் எப்படி செலவு பண்றீங்க"
        query = "நன்கொடை பணம் எப்படி செலவு பண்றீங்க"
        intent, lang, confidence = self.classifier.classify(query, "ta")
        self.assertEqual(intent, "DONATION_USAGE")
        self.assertGreaterEqual(confidence, 0.70)
        
        turn_res = ConversationManager.process_turn(self.db, session_id, query, lang, intent, confidence)
        self.assertEqual(turn_res["intent"], "DONATION_USAGE")
        self.assertFalse(turn_res["is_escalated"])
        self.assertIn("நன்கொடை பணம்", turn_res["response_text"])
        print(f"PASS: FAQ query resolved by AI with confidence {confidence}.")

    def test_04_backend_api_turn(self):
        print("\n[TEST 4] Testing Backend API Query Turn (UPI Payment Link in Tamil)...")
        session_res = ConversationManager.start_outbound_call(self.db, "+91 98765 43210", language="ta")
        session_id = session_res["session_id"]
        
        # Customer says: "எனக்கு ஜிபே பேமெண்ட் லிங்க் அனுப்புங்க"
        query = "எனக்கு ஜிபே பேமெண்ட் லிங்க் அனுப்புங்க"
        intent, lang, confidence = self.classifier.classify(query, "ta")
        self.assertEqual(intent, "PAYMENT_LINK")
        
        turn_res = ConversationManager.process_turn(self.db, session_id, query, lang, intent, confidence)
        self.assertEqual(turn_res["intent"], "PAYMENT_LINK")
        self.assertFalse(turn_res["is_tts"]) # Pre-recorded MP3 response
        self.assertIn("payment_link.mp3", turn_res["audio_url"])
        print(f"PASS: Payment link pre-recorded human MP3 voice response retrieved successfully.")

    def test_05_clarification_turn(self):
        print("\n[TEST 5] Testing Clarification Question Loop on Low Confidence Query...")
        session_res = ConversationManager.start_outbound_call(self.db, "+91 98765 43210", language="ta")
        session_id = session_res["session_id"]
        
        # Ambiguous query
        query = "xyz abcd qwerty ambiguous input"
        intent, lang, confidence = self.classifier.classify(query, "ta")
        
        turn_res = ConversationManager.process_turn(self.db, session_id, query, lang, intent, confidence)
        self.assertIn("மன்னிக்கவும்", turn_res["response_text"])
        self.assertFalse(turn_res["is_escalated"])
        print(f"PASS: AI asked clarification question to customer.")

    def test_06_human_agent_escalation(self):
        print("\n[TEST 6] Testing Human Agent Escalation (Complaint & Context Transfer)...")
        session_res = ConversationManager.start_outbound_call(self.db, "+91 98765 43210", language="ta")
        session_id = session_res["session_id"]
        
        # Customer says: "அதிகாரி கிட்ட பேசுறேன் ஏஜென்ட் கிட்ட மாத்துங்க"
        query = "அதிகாரி கிட்ட பேசுறேன் ஏஜென்ட் கிட்ட மாத்துங்க"
        intent, lang, confidence = self.classifier.classify(query, "ta")
        self.assertEqual(intent, "AGENT_REQUEST")
        
        turn_res = ConversationManager.process_turn(self.db, session_id, query, lang, intent, confidence)
        self.assertTrue(turn_res["is_escalated"])
        self.assertIsNotNone(turn_res["escalation_reason"])
        
        # Verify ticket in Agent Escalation table
        ticket = self.db.query(AgentEscalation).filter(AgentEscalation.session_id == session_id).first()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.phone, "+91 98765 43210")
        self.assertIn("requested a human agent", ticket.escalation_reason)
        print(f"PASS: Call escalated successfully. Ticket #{ticket.id} created for human agent.")

if __name__ == "__main__":
    unittest.main()
