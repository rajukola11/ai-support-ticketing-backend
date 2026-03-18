import uuid
import enum

from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class TicketStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(enum.Enum):
    GENERAL = "general"
    BILLING = "billing"
    TECHNICAL = "technical"
    OTHER = "other"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    status = Column(Enum(TicketStatus), nullable=False, default=TicketStatus.OPEN)
    priority = Column(Enum(TicketPriority), nullable=False, default=TicketPriority.MEDIUM)
    category = Column(Enum(TicketCategory), nullable=False, default=TicketCategory.GENERAL)

    # Owner — the user who created the ticket
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Agent assigned to handle the ticket (optional)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[user_id], backref="tickets")
    assignee = relationship("User", foreign_keys=[assigned_to])