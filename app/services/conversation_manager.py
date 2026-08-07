import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.config import INTENTS_REGISTRY, HIGH_CONFIDENCE_THRESHOLD, CLARIFICATION_THRESHOLD
from app.models import CallSessionModel, CallTurnModel, AgentEscalation, QueryLog, CustomerProfile
from app.services.backend_api import BackendAPIService
from app.services.tts_service import DynamicTTSService
from app.services.audio_retrieval import AudioRetrievalService

logger = logging.getLogger(__name__)

# Active In-Memory Call Sessions Cache
ACTIVE_OUTBOUND_CALLS: Dict[str, Dict[str, Any]] = {}

class ConversationManager:
    @staticmethod
    def start_outbound_call(
        db: Session,
        customer_phone: str = "+91 98765 43210",
        campaign_id: Optional[int] = 1,
        language: str = "ta"
    ) -> Dict[str, Any]:
        """Initiates an outbound call session with customer greeting."""
        session_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"
        
        customer = BackendAPIService.get_customer_by_phone(db, customer_phone)
        customer_name = customer.get("name_ta") if language == "ta" else customer.get("name_en")

        session_data = {
            "session_id": session_id,
            "campaign_id": campaign_id,
            "customer_id": customer.get("customer_id"),
            "customer_name": customer_name,
            "phone": customer_phone,
            "policy_number": customer.get("policy_number"),
            "language": language,
            "status": "CONNECTED",
            "start_time": time.time(),
            "turn_count": 0,
            "clarification_count": 0,
            "history": [],
            "escalated": False
        }
        ACTIVE_OUTBOUND_CALLS[session_id] = session_data

        # Save session to DB
        db_session = CallSessionModel(
            session_id=session_id,
            campaign_id=campaign_id,
            customer_id=customer.get("customer_id"),
            customer_name=customer_name,
            phone=customer_phone,
            language=language,
            status="CONNECTED"
        )
        db.add(db_session)
        db.commit()

        greeting_info = INTENTS_REGISTRY.get("GREETING", {})
        greeting_text = (
            f"வணக்கம் {customer_name}! எங்கள் குழந்தைகள் இல்ல அறக்கட்டளையிலிருந்து அழைக்கிறோம். ஆதரவற்ற 200+ குழந்தைகளின் கல்வி மற்றும் உணவு உதவி தொடர்பாக பேசுகிறோம்."
            if language == "ta" else
            f"Hello {customer.get('name_en')}! Calling from our children's home foundation regarding support for orphaned children's education and nutrition."
        )

        # Generate audio url
        audio_service = AudioRetrievalService()
        rel_audio, _ = audio_service.get_audio_path("GREETING", language)

        return {
            "session_id": session_id,
            "status": "CONNECTED",
            "customer": customer,
            "greeting_text": greeting_text,
            "greeting_audio_url": f"/{rel_audio}",
            "message": "Outbound call connected successfully."
        }

    @staticmethod
    def process_turn(
        db: Session,
        session_id: str,
        transcription: str,
        detected_lang: str,
        intent_code: str,
        confidence: float
    ) -> Dict[str, Any]:
        """
        Decision Engine processing for a single conversation turn:
        1. Context & Multi-turn state update
        2. Escalation triggers (Explicit Agent Request / Complaint / Low Confidence)
        3. Backend API personalization (Policy, Premium, Payment Link, EMI, Address)
        4. Audio response selection (Approved Pre-recorded vs Dynamic TTS)
        5. Clarification loop logic
        """
        start_time = time.time()
        session = ACTIVE_OUTBOUND_CALLS.get(session_id)

        # If session not in memory, reconstruct or default
        if not session:
            customer = BackendAPIService.get_customer_by_phone(db, "+91 98765 43210")
            session = {
                "session_id": session_id,
                "customer_id": customer.get("customer_id"),
                "customer_name": customer.get("name_ta"),
                "phone": customer.get("phone"),
                "policy_number": customer.get("policy_number"),
                "language": detected_lang,
                "status": "CONNECTED",
                "start_time": time.time(),
                "turn_count": 0,
                "clarification_count": 0,
                "history": [],
                "escalated": False
            }
            ACTIVE_OUTBOUND_CALLS[session_id] = session

        session["turn_count"] += 1
        turn_num = session["turn_count"]

        # Fetch Customer details for Backend API lookups
        customer = BackendAPIService.get_customer_by_phone(db, session["phone"])
        policy_no = customer.get("policy_number")
        premium_amt = customer.get("premium_amount")
        due_date = customer.get("due_date")

        escalate = False
        escalation_reason = None
        response_text = ""
        is_tts = False
        audio_url = ""

        # --- RULE 1: Direct Escalation Triggers ---
        if intent_code == "AGENT_REQUEST":
            escalate = True
            escalation_reason = "Customer explicitly requested a human agent."
            response_text = "நிச்சயமாக. உங்கள் அழைப்பை உடனடி வாடிக்கையாளர் உதவி முகவரிடம் மாற்றுகிறேன், தயவுசெய்து காத்திருக்கவும்."
            audio_url = "/audio/ta/supervisor_escalation.mp3"

        elif intent_code == "COMPLAINT":
            escalate = True
            escalation_reason = "Customer grievance/complaint detected."
            response_text = "உங்கள் புகாரை நாங்கள் தீவிரமாக எடுத்துக்கொள்கிறோம். உங்கள் அழைப்பை மேலதிகாரியிடம் மாற்றுகிறேன்."
            audio_url = "/audio/ta/supervisor_escalation.mp3"

        elif confidence < CLARIFICATION_THRESHOLD and session["clarification_count"] >= 1:
            escalate = True
            escalation_reason = f"Low confidence score ({confidence}) after clarification attempt."
            response_text = "மன்னிக்கவும். உங்கள் வினவலுக்கு துல்லியமான பதிலளிக்க உங்கள் அழைப்பை எங்கள் வாடிக்கையாளர் முகவரிடம் மாற்றுகிறேன்."
            audio_url = "/audio/ta/supervisor_escalation.mp3"

        # --- RULE 2: Clarification Trigger ---
        elif confidence < CLARIFICATION_THRESHOLD or intent_code == "FALLBACK_UNKNOWN":
            session["clarification_count"] += 1
            response_text = "மன்னிக்கவும், தாங்கள் கூறியதை என்னால் தெளிவாக விளங்கிக்கொள்ள முடியவில்லை. உங்கள் பாலிசி விவரம் அல்லது பிரீமியம் தவணை தொகை பற்றியா?"
            rel_path, _ = AudioRetrievalService().get_audio_path("FALLBACK_UNKNOWN", detected_lang)
            audio_url = f"/{rel_path}"

        # --- RULE 3: High Confidence FAQ & Backend API Response Generator ---
        else:
            session["clarification_count"] = 0 # Reset clarification on good match
            
            if intent_code == "POLICY_ENQUIRY":
                policy_info = BackendAPIService.get_policy_details(db, policy_no)
                response_text = f"உங்கள் பாலிசி {policy_info['policy_number']} தற்போது செயலில் உள்ளது. இதற்கான காப்பீட்டுத் தொகை ரூபாய் {int(policy_info['sum_assured']):,}. வருமான வரி விலக்கு சலுகையும் உண்டு."
                rel_url, _ = DynamicTTSService.generate_tts_audio(response_text, detected_lang)
                audio_url = f"/{rel_url}"
                is_tts = True

            elif intent_code == "PREMIUM_DUE":
                response_text = f"உங்கள் அடுத்த பாலிசி தவணைத் தொகை ரூபாய் {int(premium_amt):,}. செலுத்த வேண்டிய கடைசி தேதி {due_date}."
                rel_url, _ = DynamicTTSService.generate_tts_audio(response_text, detected_lang)
                audio_url = f"/{rel_url}"
                is_tts = True

            elif intent_code == "PAYMENT_LINK":
                link = BackendAPIService.generate_payment_link(session["phone"], policy_no, premium_amt)
                response_text = f"உங்கள் மொபைல் எண்ணிற்கு ஆன்லைனில் கட்டணம் செலுத்த SMS மூலம் லிங்க் அனுப்பியுள்ளேன். UPI அல்லது கார்டு மூலம் உடனடியாக செலுத்தலாம்."
                rel_url, _ = DynamicTTSService.generate_tts_audio(response_text, detected_lang)
                audio_url = f"/{rel_url}"
                is_tts = True

            elif intent_code == "EMI_OPTIONS":
                emi = BackendAPIService.calculate_emi_options(premium_amt)
                response_text = f"உங்கள் பிரீமியம் தொகையை மாதம் ரூபாய் {int(emi['monthly_emi']):,} என்ற எளிய மாத தவணையாக (EMI) மாற்றி செலுத்தலாம்."
                rel_url, _ = DynamicTTSService.generate_tts_audio(response_text, detected_lang)
                audio_url = f"/{rel_url}"
                is_tts = True

            elif intent_code == "ADDRESS_UPDATE":
                response_text = "உங்கள் முகவரி மாற்றக் கோரிக்கை பதிவு செய்யப்பட்டது. சரிபார்ப்பிற்காக SMS மூலம் விபரக் படிவம் அனுப்பப்பட்டுள்ளது."
                rel_url, _ = AudioRetrievalService().get_audio_path("ADDRESS_UPDATE", detected_lang)
                audio_url = f"/{rel_url}"

            elif intent_code == "CALLBACK_REQUEST":
                response_text = "சரி, உங்கள் அழைப்புக் கோரிக்கை பதிவு செய்யப்பட்டது. எங்கள் மேலாளர் உங்களுக்கு வசதியான நேரத்தில் தொடர்புகொள்வார்."
                rel_url, _ = AudioRetrievalService().get_audio_path("CALLBACK_REQUEST", detected_lang)
                audio_url = f"/{rel_url}"

            elif intent_code in INTENTS_REGISTRY:
                intent_info = INTENTS_REGISTRY[intent_code]
                response_text = intent_info.get("chunk_ta") if detected_lang == "ta" else intent_info.get("chunk_en")
                rel_path, _ = AudioRetrievalService().get_audio_path(intent_code, detected_lang)
                audio_url = f"/{rel_path}"

            else:
                response_text = "உங்கள் வினவல் பதிவு செய்யப்பட்டது."
                audio_url = "/audio/ta/greeting.mp3"

        # Update Session History
        turn_entry = {
            "turn": turn_num,
            "customer_speech": transcription,
            "intent": intent_code,
            "confidence": confidence,
            "response_text": response_text,
            "escalated": escalate
        }
        session["history"].append(turn_entry)

        # Handle Agent Escalation Creation in DB
        if escalate:
            session["escalated"] = True
            session["status"] = "ESCALATED"
            
            # Format transcript history summary
            conv_summary = f"Customer Query: '{transcription}'. Identified Intent: {intent_code} (Conf: {confidence}). Escalation Reason: {escalation_reason}."
            past_responses = " | ".join([t["response_text"] for t in session["history"]])

            escalation_ticket = AgentEscalation(
                session_id=session_id,
                customer_id=customer.get("customer_id"),
                customer_name=customer.get("name_ta") or customer.get("name_en"),
                phone=session["phone"],
                policy_number=policy_no,
                intent=intent_code,
                confidence_score=confidence,
                conversation_summary=conv_summary,
                responses_provided=past_responses,
                escalation_reason=escalation_reason,
                status="PENDING"
            )
            db.add(escalation_ticket)

            # Update CallSessionModel in DB
            db_sess = db.query(CallSessionModel).filter(CallSessionModel.session_id == session_id).first()
            if db_sess:
                db_sess.status = "ESCALATED"
                db_sess.escalated = True
                db_sess.escalation_reason = escalation_reason

        # Record Turn in DB
        db_turn = CallTurnModel(
            session_id=session_id,
            turn_number=turn_num,
            customer_speech=transcription,
            transcription=transcription,
            classified_intent=intent_code,
            confidence_score=confidence,
            response_text=response_text,
            audio_url=audio_url,
            is_tts=is_tts,
            escalated=escalate
        )
        db.add(db_turn)
        db.commit()

        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        intent_name = INTENTS_REGISTRY.get(intent_code, {}).get("name", "Supervisor Escalation")

        return {
            "session_id": session_id,
            "turn_number": turn_num,
            "transcription": transcription,
            "language": detected_lang,
            "intent": intent_code,
            "intent_name": intent_name,
            "confidence": confidence,
            "response_text": response_text,
            "audio_url": audio_url,
            "is_tts": is_tts,
            "is_escalated": escalate,
            "escalation_reason": escalation_reason,
            "processing_time_ms": processing_time_ms
        }
