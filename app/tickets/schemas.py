from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.tickets.models import TicketStatus, TicketPriority, TicketCategory


# -----------------------------
# Create Ticket
# -----------------------------
class TicketCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    priority: TicketPriority = TicketPriority.MEDIUM
    category: TicketCategory = TicketCategory.GENERAL


# -----------------------------
# Update Ticket (all optional)
# -----------------------------
class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    priority: Optional[TicketPriority] = None
    category: Optional[TicketCategory] = None
    status: Optional[TicketStatus] = None
    assigned_to: Optional[UUID] = None


# -----------------------------
# Ticket Response
# -----------------------------
class TicketResponse(BaseModel):
    id: UUID
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    user_id: UUID
    assigned_to: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# -----------------------------
# Ticket List Response (summary)
# -----------------------------
class TicketListResponse(BaseModel):
    id: UUID
    title: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True