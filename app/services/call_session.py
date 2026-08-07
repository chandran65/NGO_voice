import uuid
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import SupervisorCallback, QueryLog
from app.config import INTENTS_REGISTRY

logger = logging.getLogger(__name__)

# Active In-Memory Call Sessions Registry
ACTIVE_CALL_SESSIONS: Dict[str, Dict[str, Any]] = {}

class CallSessionManager:
    @staticmethod
    def start_session(donor_phone: str = "+91 98765 43210", language: str = "ta") -> Dict[str, Any]:
        session_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"
        session_data = {
            "session_id": session_id,
            "donor_phone": donor_phone,
            "language": language,
            "status": "CONNECTED",
            "start_time": time.time(),
            "transcript_history": [],
            "escalated": False
        }
        ACTIVE_CALL_SESSIONS[session_id] = session_data

        greeting_text = (
            "வணக்கம்! எங்கள் குழந்தைகள் இல்ல அறக்கட்டளையிலிருந்து அழைக்கிறோம். உங்களுக்கு எவ்வாறு உதவலாம்?"
            if language == "ta" else
            "Hello! Calling from our children's home foundation. How can we assist your donation inquiry today?"
        )
        
        greeting_audio = (
            f"/audio/{language}/greeting.mp3" if language == "ta" else f"/audio/en/greeting.mp3"
        )

        return {
            "call_session_id": session_id,
            "status": "CONNECTED",
            "greeting_text": greeting_text,
            "greeting_audio_url": greeting_audio,
            "message": "Outbound call connected successfully."
        }

    @staticmethod
    def handle_supervisor_escalation(
        db: Session,
        session_id: str,
        unmapped_query: str,
        language: str = "ta",
        donor_phone: str = "+91 98765 43210"
    ) -> SupervisorCallback:
        """Creates a pending Supervisor Callback ticket in SQLite."""
        ticket = SupervisorCallback(
            call_session_id=session_id,
            donor_phone=donor_phone,
            unmapped_query=unmapped_query,
            language=language,
            expected_callback_by="In 3 to 5 minutes",
            status="PENDING"
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        logger.info(f"Created Supervisor Callback Ticket #{ticket.id} for session {session_id}")
        return ticket

    @staticmethod
    def end_session(session_id: str) -> Dict[str, Any]:
        if session_id in ACTIVE_CALL_SESSIONS:
            session = ACTIVE_CALL_SESSIONS.pop(session_id)
            duration_sec = round(time.time() - session["start_time"], 1)
            return {
                "session_id": session_id,
                "status": "ENDED",
                "duration_seconds": duration_sec,
                "escalated": session["escalated"]
            }
        return {"session_id": session_id, "status": "NOT_FOUND"}
