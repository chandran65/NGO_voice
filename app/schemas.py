from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class VoiceProcessResponse(BaseModel):
    transcription: str = Field(..., description="Speech to text output")
    language: str = Field(..., description="ISO language code ('en' or 'ta')")
    language_name: str = Field(..., description="Human readable language name")
    intent: str = Field(..., description="Classified intent code")
    intent_name: str = Field(..., description="Human readable intent name")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    audio: str = Field(..., description="Relative audio path, e.g., 'audio/ta/donation_usage.mp3'")
    audio_url: str = Field(..., description="Full endpoint URL to stream audio")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    is_escalated: bool = Field(False, description="True if escalated to supervisor")

class TextProcessRequest(BaseModel):
    text: str = Field(..., description="Input query text", min_length=1)
    force_language: Optional[str] = Field(None, description="Optional forced language code ('en' or 'ta')")

class CallStartRequest(BaseModel):
    donor_phone: str = Field("+91 98765 43210", description="Phone number of donor being called")
    language: str = Field("ta", description="Preferred call language ('ta' or 'en')")

class CallStartResponse(BaseModel):
    call_session_id: str
    status: str
    greeting_text: str
    greeting_audio_url: str
    message: str

class SupervisorCallbackSchema(BaseModel):
    id: int
    call_session_id: str
    donor_phone: str
    unmapped_query: str
    language: str
    created_at: datetime
    expected_callback_by: str
    status: str

    class Config:
        from_attributes = True

class IntentResponseSchema(BaseModel):
    intent_code: str
    name: str
    description_en: str
    description_ta: str
    file_name: str
    audio_url_en: str
    audio_url_ta: str

class QueryLogSchema(BaseModel):
    id: int
    timestamp: datetime
    source_type: str
    transcription: str
    detected_language: str
    classified_intent: str
    confidence_score: float
    audio_relative_path: str
    processing_time_ms: float

    class Config:
        from_attributes = True

class CampaignSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    total_customers: int
    completed_calls: int
    escalated_calls: int

    class Config:
        from_attributes = True

class CustomerProfileSchema(BaseModel):
    id: int
    customer_id: str
    phone: str
    name_ta: str
    name_en: str
    policy_number: str
    plan_type: str
    premium_amount: float
    due_date: str
    sum_assured: float
    address: str
    email: Optional[str] = None

    class Config:
        from_attributes = True

class OutboundCallTurnResponse(BaseModel):
    session_id: str
    turn_number: int
    transcription: str
    language: str
    intent: str
    intent_name: str
    confidence: float
    response_text: str
    audio_url: str
    is_tts: bool
    is_escalated: bool
    escalation_reason: Optional[str] = None
    processing_time_ms: float

class AgentEscalationSchema(BaseModel):
    id: int
    session_id: str
    customer_id: Optional[str] = None
    customer_name: str
    phone: str
    policy_number: Optional[str] = None
    intent: str
    confidence_score: float
    conversation_summary: str
    responses_provided: str
    escalation_reason: str
    status: str
    agent_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

