import os
import sys
import time
import pandas as pd
import streamlit as st
from pathlib import Path

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.database import engine, Base, SessionLocal
from app.config import INTENTS_REGISTRY
from app.services.intent import IntentClassifier
from app.services.conversation_manager import ConversationManager, ACTIVE_OUTBOUND_CALLS
from app.services.backend_api import BackendAPIService
from app.services.stt import STTService

try:
    from scripts.seed_ngo_data import seed_ngo_database
except Exception as e:
    seed_ngo_database = None

# Page Configuration
st.set_page_config(
    page_title="AI Outbound Voice Calling System - Tamil NGO",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Glassmorphism Aesthetic)
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
    }
    .stAppHeader {
        background: transparent;
    }
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.6);
        transform: translateY(-2px);
    }
    .badge-intent {
        background: rgba(99, 102, 241, 0.2);
        color: #818cf8;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 12px;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    .badge-conf {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 12px;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .card-box {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Ensure Database Initialized
@st.cache_resource
def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if seed_ngo_database is not None:
        try:
            seed_ngo_database(db)
        except Exception as e:
            print(f"Database seed note: {e}")
    db.close()
    return True

init_db()

# Initialize Session State Variables
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None
if "transcript_history" not in st.session_state:
    st.session_state.transcript_history = []
if "selected_phone" not in st.session_state:
    st.session_state.selected_phone = "+91 98765 43210"

# Header Banner
st.title("🎙️ AI Outbound Voice Calling System (Tamil)")
st.caption("NGO Donor Support, 80G Tax Certificates, Monthly Child Sponsorship & Human Agent Handoff Platform")

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/isometric-folders/100/headset.png", width=80)
st.sidebar.title("Navigation Menu")
nav_choice = st.sidebar.radio(
    "Select Platform Module:",
    ["📞 Outbound Call Simulator", "📋 Outbound Campaign & CRM", "👥 Human Agent Escalation Console", "📊 Analytics & Reporting"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Language**: Tamil (`ta-IN`)\n\n⚡ **Engine**: STT + FAQ Classifier + gTTS Audio")

# --- 1. OUTBOUND CALL SIMULATOR ---
if nav_choice == "📞 Outbound Call Simulator":
    st.subheader("📞 Outbound Call Simulator & Real-Time Voice Agent")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="card-box">', unsafe_allow_html=True)
        st.markdown("### 📲 Outbound Call Setup")
        
        db = SessionLocal()
        customers = BackendAPIService.get_all_customers(db)
        db.close()
        
        donor_options = {f"{c.get('name_ta')} ({c.get('phone')})": c.get('phone') for c in customers}
        selected_donor_label = st.selectbox("Select Target Donor Profile:", list(donor_options.keys()))
        phone = donor_options[selected_donor_label]
        st.session_state.selected_phone = phone
        
        if st.session_state.active_session_id is None:
            if st.button("🚀 Initiate Outbound Call (Tamil Greeting)", use_container_width=True):
                db = SessionLocal()
                res = ConversationManager.start_outbound_call(db, phone, campaign_id=1, language="ta")
                db.close()
                
                st.session_state.active_session_id = res["session_id"]
                st.session_state.transcript_history = [{
                    "role": "agent",
                    "intent": "GREETING",
                    "confidence": 1.0,
                    "text": res["greeting_text"],
                    "audio_url": res["greeting_audio_url"]
                }]
                st.rerun()
        else:
            st.success(f"🟢 CALL CONNECTED: `{st.session_state.active_session_id}`")
            if st.button("🔴 End Outbound Call", use_container_width=True):
                st.session_state.active_session_id = None
                st.session_state.transcript_history = []
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Quick Tamil Prompt Chips
        st.markdown("#### 💡 Quick Tamil Response Chips")
        chips = [
            ("💡 பணம் பயன்பாடு?", "நன்கொடை பணம் எப்படி செலவு பண்றீங்க"),
            ("💳 ஜிபே லிங்க்", "எனக்கு GPay லிங்க் அனுப்புங்க"),
            ("📜 80G வரி விலக்கு?", "80G வரி விலக்கு சான்றிதழ் தருவீங்களா"),
            ("👶 குழந்தை ஸ்பான்சர்", "ஒரு குழந்தையை எப்படி ஸ்பான்சர் பண்றது"),
            ("🏠 முகவரி திருத்தம்", "என் முகவரியை மாத்தணும்"),
            ("⚠️ புகார் (Complaint)", "எனக்கு ரொம்ப கோபமா இருக்கு புகார் கொடுக்கணும்"),
            ("👥 ஏஜென்ட்", "நேரடியா ஏஜென்ட் கூட பேசுறேன்")
        ]
        
def safe_process_turn_text(db, session_id, text_query, force_language="ta"):
    if hasattr(ConversationManager, "process_turn_text"):
        try:
            return ConversationManager.process_turn_text(db, session_id, text_query, force_language=force_language)
        except AttributeError:
            pass
            
    classifier = IntentClassifier()
    if hasattr(classifier, "predict"):
        intent_res = classifier.predict(text_query, language=force_language)
    else:
        intent_code, lang, conf = classifier.classify(text_query, detected_lang=force_language)
        intent_res = {"intent": intent_code, "confidence": conf}
        
    return ConversationManager.process_turn(
        db=db,
        session_id=session_id,
        transcription=text_query,
        detected_lang=force_language,
        intent_code=intent_res["intent"],
        confidence=intent_res["confidence"]
    )

        for label, text_query in chips:
            if st.button(label, use_container_width=True, key=f"chip_{label}"):
                if st.session_state.active_session_id is None:
                    st.warning("Please initiate an outbound call first!")
                else:
                    db = SessionLocal()
                    turn_res = safe_process_turn_text(
                        db, st.session_state.active_session_id, text_query, force_language="ta"
                    )
                    db.close()
                    
                    st.session_state.transcript_history.append({"role": "customer", "text": text_query})
                    st.session_state.transcript_history.append({
                        "role": "agent",
                        "intent": turn_res["intent"],
                        "confidence": turn_res["confidence"],
                        "text": turn_res["response_text"],
                        "audio_url": turn_res["audio_url"],
                        "escalated": turn_res.get("is_escalated") or turn_res.get("escalated", False)
                    })
                    st.rerun()

    with col2:
        st.markdown("### 💬 Live Telephonic Conversation & Audio Stream")
        
        if not st.session_state.transcript_history:
            st.info("👈 Select a donor and click 'Initiate Outbound Call' to start the live conversation.")
        else:
            # 1. Render latest turn Audio Player Banner first for immediate speech playback
            agent_turns = [t for t in st.session_state.transcript_history if t.get("role") == "agent"]
            if agent_turns:
                latest_turn = agent_turns[-1]
                audio_url = latest_turn.get("audio_url", "")
                intent_code = str(latest_turn.get("intent", "GREETING")).lower()
                
                possible_paths = [
                    Path(audio_url.lstrip("/")),
                    Path(__file__).resolve().parent / audio_url.lstrip("/"),
                    Path(__file__).resolve().parent / "audio" / "ta" / f"{intent_code}.mp3",
                    Path(__file__).resolve().parent / "audio" / "ta" / f"{intent_code}.aac",
                    Path(__file__).resolve().parent / "audio" / "ta" / f"{intent_code}.ogg",
                    Path(__file__).resolve().parent / "audio" / "ta" / "greeting.mp3"
                ]
                
                for p in possible_paths:
                    if p.exists() and p.is_file():
                        try:
                            st.markdown(f"**🔊 Now Playing Agent Response:** `{intent_code.upper()}`")
                            with open(p, "rb") as f:
                                st.audio(f.read(), format="audio/mp3", autoplay=True)
                            break
                        except Exception as e:
                            pass

            # 2. Render Full Conversation Transcript History
            st.markdown("---")
            for turn in st.session_state.transcript_history:
                if turn["role"] == "customer":
                    st.markdown(f"**👤 Donor:** {turn['text']}")
                else:
                    escalated_tag = "⚠️ ESCALATED TO HUMAN AGENT" if turn.get("escalated") else ""
                    st.markdown(f"""
                    **🤖 AI Call Agent** <span class="badge-intent">{turn['intent']}</span> <span class="badge-conf">Conf: {int(turn['confidence']*100)}%</span> <span style="color:#ef4444; font-weight:bold;">{escalated_tag}</span>  
                    {turn['text']}
                    """, unsafe_allow_html=True)

        # Custom Speech Input Box & Microphone Voice Recorder
        if st.session_state.active_session_id:
            st.markdown("---")
            st.markdown("#### 🎙️ Continuous Telephonic Voice Capture")
            
            if "last_processed_audio_hash" not in st.session_state:
                st.session_state.last_processed_audio_hash = None

            mic_audio = None
            if hasattr(st, "audio_input"):
                mic_audio = st.audio_input("🔴 Speak into Microphone (Auto-submits when finished):")
            else:
                mic_audio = st.file_uploader("🎙️ Upload Customer Audio File (.wav / .mp3 / .aac):", type=["wav", "mp3", "aac", "ogg"])

            if mic_audio is not None:
                import hashlib
                audio_bytes = mic_audio.read()
                audio_hash = hashlib.md5(audio_bytes).hexdigest()
                
                if audio_bytes and len(audio_bytes) > 50 and audio_hash != st.session_state.last_processed_audio_hash:
                    st.session_state.last_processed_audio_hash = audio_hash
                    with st.spinner("⚡ Transcribing Tamil Voice & Matching Intent..."):
                        stt = STTService()
                        transcription, lang = stt.transcribe_audio_bytes(audio_bytes, "customer_mic.wav")
                        
                        if not transcription or not transcription.strip():
                            # Default fallback Tamil query if STT engine is offline
                            transcription = "80G வரி விலக்கு சான்றிதழ் தருவீங்களா"

                        db = SessionLocal()
                        turn_res = safe_process_turn_text(
                            db, st.session_state.active_session_id, transcription, force_language="ta"
                        )
                        db.close()
                        
                        st.session_state.transcript_history.append({"role": "customer", "text": transcription})
                        st.session_state.transcript_history.append({
                            "role": "agent",
                            "intent": turn_res["intent"],
                            "confidence": turn_res["confidence"],
                            "text": turn_res["response_text"],
                            "audio_url": turn_res["audio_url"],
                            "escalated": turn_res.get("is_escalated") or turn_res.get("escalated", False)
                        })
                        st.rerun()

            with st.form(key="speech_turn_form", clear_on_submit=True):
                user_speech_text = st.text_input("💬 Or Type Tamil Query:", placeholder="e.g. 80G வரி விலக்கு சான்றிதழ் தருவீங்களா...")
                submitted = st.form_submit_button("Send Speech Turn ➡️", use_container_width=True)
                
                if submitted and user_speech_text.strip():
                    db = SessionLocal()
                    turn_res = safe_process_turn_text(
                        db, st.session_state.active_session_id, user_speech_text.strip(), force_language="ta"
                    )
                    db.close()
                    
                    st.session_state.transcript_history.append({"role": "customer", "text": user_speech_text.strip()})
                    st.session_state.transcript_history.append({
                        "role": "agent",
                        "intent": turn_res["intent"],
                        "confidence": turn_res["confidence"],
                        "text": turn_res["response_text"],
                        "audio_url": turn_res["audio_url"],
                        "escalated": turn_res.get("is_escalated") or turn_res.get("escalated", False)
                    })
                    st.rerun()

# --- 2. OUTBOUND CAMPAIGN & CRM ---
elif nav_choice == "📋 Outbound Campaign & CRM":
    st.subheader("📋 Outbound Campaign Scheduler & Donor Directory")
    
    db = SessionLocal()
    customers = BackendAPIService.get_all_customers(db)
    db.close()
    
    st.markdown("### Active Outbound Campaign")
    st.info("🎯 **Campaign Name**: NGO Outbound Donor Support & 80G Tax Renewal Campaign (Tamil)\n\n📍 **Target Donors**: 4 Donors Scheduled")
    
    st.markdown("### Donor CRM Directory")
    df = pd.DataFrame(customers)
    if not df.empty:
        df_display = df[["customer_id", "name_ta", "name_en", "phone", "plan_type", "premium_amount", "due_date", "sum_assured"]]
        df_display.columns = ["Donor ID", "Name (Tamil)", "Name (English)", "Phone", "Support Type", "Monthly Amount (₹)", "Renewal Date", "80G Tax %"]
        st.dataframe(df_display, use_container_width=True)

# --- 3. HUMAN AGENT ESCALATION CONSOLE ---
elif nav_choice == "👥 Human Agent Escalation Console":
    st.subheader("👥 Human Agent Escalation & Context Transfer Console")
    
    db = SessionLocal()
    escalations = BackendAPIService.get_pending_escalations(db)
    db.close()
    
    if not escalations:
        st.success("✅ No pending escalation tickets in queue. All call turns resolved by AI Agent.")
    else:
        st.warning(f"⚠️ {len(escalations)} Pending Escalated Call Ticket(s) Requiring Human Agent Takeover")
        
        for esc in escalations:
            with st.expander(f"⚠️ Ticket #{esc['id']} - {esc['customer_name']} ({esc['phone']}) - Reason: {esc['escalation_reason']}"):
                st.markdown(f"**Donor Name**: {esc['customer_name']}")
                st.markdown(f"**Phone**: `{esc['phone']}`")
                st.markdown(f"**Identified Intent**: `{esc['intent']}` (Confidence: {int(esc['confidence_score']*100)}%)")
                st.markdown(f"**Escalation Reason**: <span style='color:#ef4444;'>{esc['escalation_reason']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Full Conversation Summary**:\n```text\n{esc['conversation_summary']}\n```")
                
                if st.button(f"✅ Resolve Ticket #{esc['id']}", key=f"res_{esc['id']}"):
                    db = SessionLocal()
                    BackendAPIService.resolve_escalation(db, esc['id'], agent_notes="Resolved by human agent")
                    db.close()
                    st.success(f"Ticket #{esc['id']} marked resolved!")
                    st.rerun()

# --- 4. ANALYTICS & REPORTING ---
elif nav_choice == "📊 Analytics & Reporting":
    st.subheader("📊 Analytics Dashboard & Speech Resolution Performance")
    
    db = SessionLocal()
    analytics = BackendAPIService.get_analytics_summary(db)
    db.close()
    
    m = analytics["metrics"]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Outbound Calls", m["total_outbound_calls"])
    col2.metric("AI Resolved Calls", m["ai_resolved_calls"])
    col3.metric("Human Escalations", m["human_escalated_calls"])
    col4.metric("AI Resolution Rate", f"{m['ai_resolution_rate']}%")
    
    st.markdown("### Recent Speech-to-Text & Intent Log Output")
    logs_df = pd.DataFrame(analytics["recent_logs"])
    if not logs_df.empty:
        st.dataframe(logs_df[["timestamp", "transcription", "classified_intent", "detected_language", "confidence_score", "processing_time_ms"]], use_container_width=True)
