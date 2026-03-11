from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.auth import models
from app.auth.schemas import UserCreate
from app.auth.security import hash_password, verify_password


# -----------------------------
# Get User by Email
# -----------------------------
def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


# -----------------------------
# Get User by ID
# -----------------------------
def get_user_by_id(db: Session, user_id: UUID) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


# -----------------------------
# Create User
# -----------------------------
def create_user(db: Session, user_data: UserCreate) -> models.User:
    hashed_pw = hash_password(user_data.password)

    new_user = models.User(
        email=user_data.email,
        hashed_password=hashed_pw
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# -----------------------------
# Authenticate User
# -----------------------------
def authenticate_user(
    db: Session,
    email: str,
    password: str
) -> Optional[models.User]:

    user = get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    if not user.is_active:
        return None

    return user
