import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.config import INTENTS_REGISTRY, HIGH_CONFIDENCE_THRESHOLD, CLARIFICATION_THRESHOLD, MAX_CLARIFICATION_ATTEMPTS
from app.models import CallSessionModel, CallTurnModel, AgentEscalation, QueryLog, CustomerProfile
from app.services.backend_api import BackendAPIService
from app.services.tts_service import DynamicTTSService
from app.services.audio_retrieval import AudioRetrievalService
from app.services.normalizer import TextNormalizer

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
    def process_turn_text(db: Session, session_id: str, text: str, force_language: str = "ta") -> Dict[str, Any]:
        """Classifies intent from text query using Layered Intent Resolution System."""
        from app.services.layered_intent_resolver import LayeredIntentResolver
        resolver = LayeredIntentResolver()
        intent_res = resolver.resolve(text, language=force_language)
        return ConversationManager.process_turn(
            db=db,
            session_id=session_id,
            transcription=text,
            detected_lang=force_language,
            intent_code=intent_res.intent,
            confidence=intent_res.confidence,
            intent_result=intent_res
        )

    @staticmethod
    def process_turn(
        db: Session,
        session_id: str,
        transcription: str,
        detected_lang: str,
        intent_code: str,
        confidence: float,
        intent_result: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Decision Engine processing for a single conversation turn:
        1. Context & Multi-turn state update
        2. Escalation triggers (Explicit Agent Request / Complaint / Max Clarification limit)
        3. Backend API personalization
        4. Audio response selection
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

        normalized_text = intent_result.normalized_text if intent_result else TextNormalizer.normalize(transcription, detected_lang)

        # Fetch Customer details for Backend API lookups
        customer = BackendAPIService.get_customer_by_phone(db, session["phone"])
        policy_no = customer.get("policy_number")

        escalate = False
        escalation_reason = None
        response_text = ""
        is_tts = False
        audio_url = ""

        # --- RULE 1: Direct Escalation Triggers ---
        if intent_code == "AGENT_REQUEST":
            escalate = True
            escalation_reason = "Customer explicitly requested a human agent."
            response_text = "நிச்சயமாக. உங்கள் அழைப்பை அறக்கட்டளையின் நேரடி அதிகாரியிடம் மாற்றுகிறேன், தயவுசெய்து காத்திருக்கவும்."
            audio_url = "/audio/ta/supervisor_escalation.mp3"

        elif intent_code == "COMPLAINT":
            escalate = True
            escalation_reason = "Customer grievance/complaint detected."
            response_text = "உங்கள் புகாரை நாங்கள் தீவிரமாக எடுத்துக்கொள்கிறோம். உங்கள் அழைப்பை மேலதிகாரியிடம் மாற்றுகிறேன்."
            audio_url = "/audio/ta/supervisor_escalation.mp3"

        elif (confidence < CLARIFICATION_THRESHOLD or intent_code == "FALLBACK_UNKNOWN") and session["clarification_count"] >= MAX_CLARIFICATION_ATTEMPTS:
            escalate = True
            escalation_reason = f"Classification ambiguous after maximum clarification attempts ({MAX_CLARIFICATION_ATTEMPTS})."
            response_text = "மன்னிக்கவும். உங்கள் வினவலுக்கு துல்லியமான பதிலளிக்க உங்கள் அழைப்பை எங்கள் வாடிக்கையாளர் முகவரிடம் மாற்றுகிறேன்."
            audio_url = "/audio/ta/supervisor_escalation.mp3"

        # --- RULE 2: Clarification Trigger ---
        elif confidence < CLARIFICATION_THRESHOLD or intent_code == "FALLBACK_UNKNOWN":
            session["clarification_count"] += 1
            response_text = "மன்னிக்கவும், தாங்கள் கூறியதை என்னால் தெளிவாக விளங்கிக்கொள்ள முடியவில்லை. எங்கள் குழந்தைகள் இல்லத்தின் நன்கொடை விவரங்கள் அல்லது 80G வரி விலக்கு பற்றியா?"
            rel_path, _ = AudioRetrievalService().get_audio_path("FALLBACK_UNKNOWN", detected_lang)
            audio_url = f"/{rel_path}"

        # --- RULE 3: High Confidence FAQ & Approved Pre-recorded Audio Response ---
        else:
            session["clarification_count"] = 0 # Reset clarification on good match
            
            if intent_code in INTENTS_REGISTRY:
                intent_info = INTENTS_REGISTRY[intent_code]
                response_text = intent_info.get("chunk_ta") if detected_lang == "ta" else intent_info.get("chunk_en")
                rel_path, _ = AudioRetrievalService().get_audio_path(intent_code, detected_lang)
                audio_url = f"/{rel_path}"
            else:
                response_text = "உங்கள் வினவல் பதிவு செய்யப்பட்டது."
                rel_path, _ = AudioRetrievalService().get_audio_path("GREETING", detected_lang)
                audio_url = f"/{rel_path}"

        # Update Session History
        turn_entry = {
            "turn": turn_num,
            "customer_speech": transcription,
            "normalized_text": normalized_text,
            "intent": intent_code,
            "confidence": confidence,
            "method": intent_result.method if intent_result else "legacy",
            "response_text": response_text,
            "escalated": escalate
        }
        session["history"].append(turn_entry)

        # Handle Agent Escalation Creation in DB
        if escalate:
            session["escalated"] = True
            session["status"] = "ESCALATED"
            
            # Format transcript history summary including normalized transcript & classification attempts
            attempts_count = len(session["history"])
            conv_summary = (
                f"Session: {session_id} | Customer: '{transcription}' | Normalized: '{normalized_text}' | "
                f"Intent: {intent_code} (Conf: {confidence}) | Classification Attempts: {attempts_count} | "
                f"Reason: {escalation_reason}"
            )
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
