from pydantic import BaseModel,EmailStr
from uuid import UUID
from app.auth.models import UserRole
from datetime import datetime

class UserCreate(BaseModel):
    email:EmailStr
    password:str
class UserLogin(BaseModel):
    email:EmailStr
    password:str
class UserResponse(BaseModel):
    id:UUID
    email:EmailStr
    role:UserRole
    is_active:bool
    is_verified:bool
    created_at:datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str | None = None
