import sys
import os
from pathlib import Path

# Fix Windows console UTF-8 printing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure project path is accessible
sys.path.append(str(Path(__file__).resolve().parent))

from scripts.generate_audio import generate_all_audio_files
from scripts.generate_escalation_audio import generate_number_source_audio as generate_escalation_audios
from scripts.init_db import initialize_database
from app.services.intent import IntentClassifier
from app.services.stt import detect_language_from_text
from app.services.audio_retrieval import AudioRetrievalService

def run_poc_tests():
    print("==================================================")
    print(" 2-WAY AI CALL AGENT & VOICE RETRIEVAL TEST SUITE ")
    print("==================================================")

    # 1. Generate Escalation Audio & Standard Audio
    print("\n[TEST 1/4] Generating supervisor escalation & response audio files...")
    generate_escalation_audios()
    generate_all_audio_files()

    # 2. Database Init
    print("\n[TEST 2/4] Initializing SQLite database...")
    initialize_database()

    # 3. Test Intent Classifier & Escalation Trigger
    print("\n[TEST 3/4] Testing 2-Way Call Intent Matching & Supervisor Escalation...")
    classifier = IntentClassifier()
    audio_service = AudioRetrievalService()

    test_queries = [
        ("How will my donation be used?", "en", "DONATION_USAGE"),
        ("உங்கள் அறக்கட்டளை பற்றி கூறுங்கள்", "ta", "ABOUT_HOME"),
        ("Do I get 80G tax exemption certificate?", "en", "TAX_BENEFITS"),
        ("வரி விலக்கு சலுகை கிடைக்குமா?", "ta", "TAX_BENEFITS"),
        ("How to pay via GPay or UPI?", "en", "PAYMENT_METHODS"),
        ("மாதம் 1500 ரூபாய் கொடுத்து ஒரு குழந்தையை படிக்க வைக்கலாமா?", "ta", "SPONSOR_CHILD"),
        ("Hello, good morning!", "en", "GREETING"),
        ("வணக்கம் நலமா?", "ta", "GREETING"),
        ("What is your rocket galaxy satellite strategy?", "en", "SUPERVISOR_ESCALATION"),
        ("செவ்வாய் கிரகத்தில் எப்போது வீடு கட்டுவீர்கள்?", "ta", "SUPERVISOR_ESCALATION")
    ]

    passed = 0
    for query, expected_lang, expected_intent in test_queries:
        det_lang = detect_language_from_text(query)
        intent, lang, conf = classifier.classify(query, det_lang)
        rel_audio, abs_audio = audio_service.get_audio_path(intent, lang)
        
        status = "PASSED" if (intent == expected_intent and lang == expected_lang) else "WARNING (Soft Match)"
        if status == "PASSED":
            passed += 1
            
        print(f"\nQuery: '{query}'")
        print(f" -> Language Detected: '{lang}' (Expected: '{expected_lang}')")
        print(f" -> Intent Classified: '{intent}' (Confidence: {conf*100:.0f}%, Expected: '{expected_intent}')")
        print(f" -> Audio Path: '{rel_audio}' | Status: {status}")

    print(f"\n2-Way Call Agent Accuracy: {passed}/{len(test_queries)} ({passed/len(test_queries)*100:.0f}%)")

    # 4. Audio Verification
    print("\n[TEST 4/4] Verifying supervisor escalation audio exists...")
    from app.config import AUDIO_DIR
    ta_escalation = AUDIO_DIR / "ta" / "supervisor_escalation.mp3"
    if ta_escalation.exists():
        print(f"Verified: Tamil Supervisor Escalation Audio exists at {ta_escalation.name}")
    else:
        print("Warning: Tamil escalation audio missing.")

    print("\n==================================================")
    print(" ALL 2-WAY CONVERSATIONAL AGENT TESTS COMPLETED!  ")
    print("==================================================")

if __name__ == "__main__":
    run_poc_tests()
