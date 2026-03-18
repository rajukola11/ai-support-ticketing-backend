from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.ai.models import AIResultStatus


class AIResultResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    suggested_category: Optional[str] = None
    suggested_priority: Optional[str] = None
    summary: Optional[str] = None
    confidence: Optional[float] = None
    draft_response: Optional[str] = None
    status: AIResultStatus
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    applied: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AIClassifyResponse(BaseModel):
    message: str
    ai_result: AIResultResponse
    ticket_updated: bool


class AIDraftResponse(BaseModel):
    message: str
    ticket_id: UUID
    draft_response: str
    model_used: Optional[str] = None