from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class IntentResult(BaseModel):
    """
    Canonical structured representation for intent classification across the layered pipeline.
    Methods: 'rule' | 'embedding' | 'llm' | 'clarification' | 'fallback'
    """
    intent: str = Field(..., description="Classified intent code (e.g. DONATION_USAGE, PAYMENT_LINK, AGENT_REQUEST)")
    confidence: float = Field(..., description="Calibrated confidence score between 0.0 and 1.0")
    method: str = Field(..., description="Classifier method used: 'rule', 'embedding', 'llm', 'clarification', 'fallback'")
    requires_clarification: bool = Field(False, description="True if intent resolution requires a clarification question")
    requires_human: bool = Field(False, description="True if intent requires direct human agent escalation")
    normalized_text: str = Field(..., description="Language-normalized transcript used for classification")
    raw_text: str = Field(..., description="Original raw transcript from user/STT for audit and history")
    latency_ms: float = Field(0.0, description="Processing time spent in classification stage in milliseconds")
    reasoning: Optional[str] = Field(None, description="Concise diagnostic description (not exposed to user)")
    diagnostics: Dict[str, Any] = Field(default_factory=dict, description="Structured observability telemetry metadata")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
