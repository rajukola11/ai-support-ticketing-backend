from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    is_internal: bool = False  # Only agents/admins can set this to True


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class AuthorSummary(BaseModel):
    id: UUID
    email: str
    role: str

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    id: UUID
    ticket_id: UUID
    user_id: UUID
    content: str
    is_internal: bool
    created_at: datetime
    updated_at: datetime
    author: Optional[AuthorSummary] = None

    class Config:
        from_attributes = True