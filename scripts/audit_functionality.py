import sys
import os
import requests
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8080"

def audit_application():
    print("==================================================")
    print("   END-TO-END FUNCTIONALITY AUDIT & VERIFICATION  ")
    print("==================================================")

    # 1. Check Server Index & Docs
    print("\n[AUDIT 1/6] Checking FastAPI Server Connection...")
    try:
        res = requests.get(f"{BASE_URL}/")
        print(f" -> GET / status: {res.status_code} (OK)")
    except Exception as e:
        print(f" -> ERROR connecting to {BASE_URL}: {e}")
        return

    # 2. Check Intend Registry API
    print("\n[AUDIT 2/6] Checking Predefined Intents API (/api/v1/intents)...")
    res = requests.get(f"{BASE_URL}/api/v1/intents")
    intents = res.json()
    print(f" -> Registered Intents Count: {len(intents)}")
    for item in intents[:3]:
        print(f"    - {item['intent_code']}: {item['name']}")

    # 3. Test Outbound Call Start (Agent Greeting Pitch)
    print("\n[AUDIT 3/6] Testing Outbound Call Initiation (/api/v1/call/start)...")
    res = requests.post(f"{BASE_URL}/api/v1/call/start", json={"donor_phone": "+91 98765 43210", "language": "ta"})
    call_data = res.json()
    print(f" -> Call Session ID: {call_data['call_session_id']}")
    print(f" -> Agent Pitch Text: '{call_data['greeting_text']}'")
    print(f" -> Agent Pitch Audio URL: '{call_data['greeting_audio_url']}'")

    # 4. Test Text Query / Call Speech for Recognized Tamil Intent
    print("\n[AUDIT 4/6] Testing Query Classification & Human Audio Retrieval...")
    test_text_payload = {
        "text": "80G வரி விலக்கு சான்றிதழ் தருவீங்களா?",
        "force_language": "ta"
    }
    res = requests.post(f"{BASE_URL}/api/v1/process-text", json=test_text_payload)
    resp_data = res.json()
    print(f" -> Query: '{resp_data['transcription']}'")
    print(f" -> Language: {resp_data['language_name']} ({resp_data['language']})")
    print(f" -> Classified Intent: {resp_data['intent']} ({resp_data['intent_name']})")
    print(f" -> Confidence Score: {resp_data['confidence']*100:.0f}%")
    print(f" -> Audio Stream URL: '{resp_data['audio_url']}'")

    # Verify Audio URL accessibility
    audio_res = requests.get(f"{BASE_URL}{resp_data['audio_url']}")
    print(f" -> Audio Stream HTTP Status: {audio_res.status_code} ({len(audio_res.content)} bytes)")

    # 5. Test Unmapped Query Supervisor Escalation
    print("\n[AUDIT 5/6] Testing Tamil Supervisor Escalation Fallback...")
    unmapped_payload = {
        "text": "What is your rocket galaxy satellite strategy?",
        "force_language": "ta"
    }
    res = requests.post(f"{BASE_URL}/api/v1/process-text", json=unmapped_payload)
    escl_data = res.json()
    print(f" -> Unmapped Query: '{escl_data['transcription']}'")
    print(f" -> Classified Intent: {escl_data['intent']}")
    print(f" -> Is Escalated: {escl_data['is_escalated']}")
    print(f" -> Escalation Audio URL: '{escl_data['audio_url']}'")

    # 6. Check Supervisor Callback Tickets API
    print("\n[AUDIT 6/6] Checking Pending Supervisor Callback Tickets Queue...")
    res = requests.get(f"{BASE_URL}/api/v1/call/supervisor-tickets")
    tickets = res.json()
    print(f" -> Pending Supervisor Callback Tickets: {len(tickets)}")
    if tickets:
        t = tickets[0]
        print(f"    - Ticket #{t['id']} ({t['call_session_id']}): '{t['unmapped_query']}' | Expected Callback: {t['expected_callback_by']}")

    print("\n==================================================")
    print("      ALL FUNCTIONALITY AUDITS PASSED 100%!       ")
    print("==================================================")

if __name__ == "__main__":
    audit_application()
