from sqlalchemy import Column,Integer,String,Boolean,DateTime,Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid

from app.db.base import Base

class UserRole(enum.Enum):
    USER = "user"
    SUPPORT_AGENT="support_agent"
    ADMIN="admin"

class User(Base):
    __tablename__="users"
    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4,index=True)
    email = Column(String,index=True,unique=True, nullable=False)
    hashed_password=Column(String,nullable=False)
    role=Column(Enum(UserRole),nullable=False,default=UserRole.USER)
    is_active=Column(Boolean,default=True)
    is_verified=Column(Boolean,default=False)
    created_at=Column(DateTime(timezone=True),server_default=func.now())
    updated_at=Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now())