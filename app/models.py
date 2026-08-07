from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from datetime import datetime
from app.database import Base

class IntentModel(Base):
    __tablename__ = "intents"

    id = Column(Integer, primary_key=True, index=True)
    intent_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description_en = Column(Text, nullable=False)
    description_ta = Column(Text, nullable=False)
    file_name = Column(String(100), nullable=False)

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    source_type = Column(String(20), default="voice") # 'voice', 'text', 'call'
    transcription = Column(Text, nullable=False)
    detected_language = Column(String(10), nullable=False) # 'en' or 'ta'
    classified_intent = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    audio_relative_path = Column(String(255), nullable=False)
    processing_time_ms = Column(Float, nullable=False)

class SupervisorCallback(Base):
    __tablename__ = "supervisor_callbacks"

    id = Column(Integer, primary_key=True, index=True)
    call_session_id = Column(String(50), index=True, nullable=False)
    donor_phone = Column(String(20), nullable=False, default="+91 98765 43210")
    unmapped_query = Column(Text, nullable=False)
    language = Column(String(10), nullable=False, default="ta")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expected_callback_by = Column(String(50), nullable=False, default="In 3 to 5 minutes")
    status = Column(String(20), nullable=False, default="PENDING") # PENDING, IN_PROGRESS, RESOLVED

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="ACTIVE") # DRAFT, ACTIVE, COMPLETED
    created_at = Column(DateTime, default=datetime.utcnow)
    total_customers = Column(Integer, default=0)
    completed_calls = Column(Integer, default=0)
    escalated_calls = Column(Integer, default=0)

class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(50), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=False)
    name_ta = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    policy_number = Column(String(50), nullable=False)
    plan_type = Column(String(100), nullable=False)
    premium_amount = Column(Float, nullable=False)
    due_date = Column(String(50), nullable=False)
    sum_assured = Column(Float, nullable=False, default=500000.0)
    address = Column(Text, nullable=False)
    email = Column(String(100), nullable=True)

class CallSessionModel(Base):
    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True, nullable=False)
    campaign_id = Column(Integer, nullable=True)
    customer_id = Column(String(50), nullable=True)
    customer_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=False)
    language = Column(String(10), default="ta")
    status = Column(String(30), default="CONNECTED") # CONNECTED, COMPLETED, ESCALATED, FAILED
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_turns = Column(Integer, default=0)
    escalated = Column(Boolean, default=False)
    escalation_reason = Column(String(255), nullable=True)

class CallTurnModel(Base):
    __tablename__ = "call_turns"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True, nullable=False)
    turn_number = Column(Integer, nullable=False)
    customer_speech = Column(Text, nullable=True)
    transcription = Column(Text, nullable=True)
    classified_intent = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    response_text = Column(Text, nullable=False)
    audio_url = Column(String(255), nullable=False)
    is_tts = Column(Boolean, default=False)
    escalated = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AgentEscalation(Base):
    __tablename__ = "agent_escalations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True, nullable=False)
    customer_id = Column(String(50), nullable=True)
    customer_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    policy_number = Column(String(50), nullable=True)
    intent = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    conversation_summary = Column(Text, nullable=False)
    responses_provided = Column(Text, nullable=False)
    escalation_reason = Column(String(255), nullable=False)
    status = Column(String(20), default="PENDING") # PENDING, IN_PROGRESS, RESOLVED
    agent_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

