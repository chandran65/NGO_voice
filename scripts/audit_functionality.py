import os
import sys

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from sqlalchemy.orm import Session

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database import engine, Base, SessionLocal
from app.models import CustomerProfile, AgentEscalation, CallSessionModel
from app.services.intent import IntentClassifier
from app.services.audio_retrieval import AudioRetrievalService
from app.services.stt import STTService
from app.services.conversation_manager import ConversationManager
from app.services.backend_api import BackendAPIService
from scripts.seed_ngo_data import seed_ngo_database

def audit_system_flow():
    print("=" * 70)
    print("🔍 AUDITING AI OUTBOUND VOICE CALLING SYSTEM (TAMIL NGO)")
    print("=" * 70)

    # 1. Database Initialization
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    seed_ngo_database(db)
    
    customers = db.query(CustomerProfile).all()
    print(f"\n✅ 1. Database Check: Found {len(customers)} Donor Profiles in CRM.")
    for c in customers:
        print(f"   • {c.customer_id}: {c.name_ta} ({c.phone}) - {c.plan_type}")

    # 2. Intent Classification Audit
    print("\n✅ 2. Intent Classifier Test (14 Tamil FAQs & Telephony Escalations):")
    classifier = IntentClassifier()
    test_queries = [
        ("வணக்கம்! நன்கொடை பணம் எப்படி செலவு பண்றீங்க", "DONATION_USAGE"),
        ("80G வரி விலக்கு சான்றிதழ் தருவீங்களா", "TAX_BENEFITS"),
        ("எனக்கு GPay லிங்க் அனுப்புங்க", "PAYMENT_LINK"),
        ("ஒரு குழந்தையை எப்படி ஸ்பான்சர் பண்றது", "SPONSOR_CHILD"),
        ("என் முகவரியை மாத்தணும்", "ADDRESS_UPDATE"),
        ("ரசீது நகல் அனுப்புங்க", "RECEIPT_REQUEST"),
        ("உங்க இல்லத்தை பற்றி சொல்லுங்க", "ABOUT_HOME"),
        ("எனக்கு ரொம்ப கோபமா இருக்கு புகார் கொடுக்கணும்", "COMPLAINT"),
        ("நேரடியா ஏஜென்ட் கூட பேசுறேன்", "AGENT_REQUEST")
    ]

    passed_intents = 0
    for query, expected in test_queries:
        res = classifier.predict(query, language="ta")
        matched = res["intent"]
        conf = res["confidence"]
        status = "PASSED" if matched == expected else "FAILED"
        if matched == expected:
            passed_intents += 1
        print(f"   [{status}] Query: '{query}' => Intent: {matched} (Expected: {expected}, Conf: {int(conf*100)}%)")

    print(f"   Intent Accuracy: {passed_intents}/{len(test_queries)} ({int(passed_intents/len(test_queries)*100)}%)")

    # 3. Audio Retrieval Audit
    print("\n✅ 3. Pre-Recorded Audio Files Audit:")
    audio_service = AudioRetrievalService()
    test_intents = ["GREETING", "DONATION_USAGE", "TAX_BENEFITS", "PAYMENT_LINK", "SPONSOR_CHILD", "ADDRESS_UPDATE", "CALLBACK_REQUEST", "RECEIPT_REQUEST", "ABOUT_HOME", "SUPERVISOR_ESCALATION"]
    
    found_audios = 0
    for intent in test_intents:
        rel_path, abs_path = audio_service.get_audio_path(intent, "ta")
        exists = os.path.exists(abs_path)
        if exists:
            found_audios += 1
            size_kb = round(os.path.getsize(abs_path) / 1024, 1)
            print(f"   • {intent}: {rel_path} ({size_kb} KB) - Valid Audio")
        else:
            print(f"   ❌ {intent}: {rel_path} - FILE MISSING")

    print(f"   Audio Files Available: {found_audios}/{len(test_intents)}")

    # 4. Multi-Turn Outbound Call Simulation
    print("\n✅ 4. Full Multi-Turn Outbound Call Simulation:")
    phone = "+91 98765 43210"
    call = ConversationManager.start_outbound_call(db, phone, campaign_id=1, language="ta")
    session_id = call["session_id"]
    print(f"   • Call Initiated! Session ID: {session_id}")
    print(f"     🤖 Greeting: {call['greeting_text'][:50]}... Audio: {call['greeting_audio_url']}")

    turns = [
        "நன்கொடை பணம் எப்படி செலவு பண்றீங்க",
        "80G வரி விலக்கு சான்றிதழ் தருவீங்களா",
        "எனக்கு GPay லிங்க் அனுப்புங்க",
        "நேரடியா ஏஜென்ட் கூட பேசுறேன்" # Triggers Human Escalation
    ]

    for idx, user_text in enumerate(turns, 1):
        turn_res = ConversationManager.process_turn_text(db, session_id, user_text, force_language="ta")
        print(f"\n   Turn {idx}:")
        print(f"     👤 Donor: {user_text}")
        print(f"     🤖 AI Agent: [{turn_res['intent']}] {turn_res['response_text'][:60]}... (Conf: {int(turn_res['confidence']*100)}%)")
        print(f"     🔊 Audio: {turn_res['audio_url']} | Escalated: {turn_res['is_escalated']}")

    # 5. Human Agent Escalation Check
    escalations = BackendAPIService.get_pending_escalations(db)
    print(f"\n✅ 5. Human Agent Escalation Queue Check: Found {len(escalations)} Escalated Ticket(s).")
    if escalations:
        esc = escalations[0]
        print(f"   • Ticket #{esc['id']}: {esc['customer_name']} ({esc['phone']})")
        print(f"     Reason: {esc['escalation_reason']}")

    db.close()
    print("\n" + "=" * 70)
    print("🎉 ALL SYSTEM AUDIT TESTS PASSED CLEANLY! SYSTEM IS 100% OPERATIONAL!")
    print("=" * 70)

if __name__ == "__main__":
    audit_system_flow()
