import uuid
import enum

from sqlalchemy import Column, String, Float, Text, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class AIResultStatus(enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"


class AIResult(Base):
    __tablename__ = "ai_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)

    # Classification results
    suggested_category = Column(String, nullable=True)
    suggested_priority = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)

    # Meta
    status = Column(Enum(AIResultStatus), nullable=False, default=AIResultStatus.SUCCESS)
    error_message = Column(Text, nullable=True)
    model_used = Column(String, nullable=True)

    # Was the suggestion applied to the ticket?
    applied = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    ticket = relationship("Ticket", backref="ai_results")