from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

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


# -----------------------------
# Store Refresh Token
# -----------------------------
def store_refresh_token(
    db: Session,
    user_id: UUID,
    token: str,
    expires_at: datetime
) -> models.RefreshToken:
    refresh_token = models.RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


# -----------------------------
# Get Valid Refresh Token
# -----------------------------
def get_valid_refresh_token(
    db: Session,
    token: str
) -> Optional[models.RefreshToken]:
    record = (
        db.query(models.RefreshToken)
        .filter(
            models.RefreshToken.token == token,
            models.RefreshToken.is_revoked == False,
        )
        .first()
    )

    if not record:
        return None

    # Check expiry in Python (timezone-aware comparison)
    if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None

    return record


# -----------------------------
# Revoke Refresh Token (logout)
# -----------------------------
def revoke_refresh_token(db: Session, token: str) -> bool:
    record = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token == token)
        .first()
    )

    if not record:
        return False

    record.is_revoked = True
    db.commit()
    return True


# -----------------------------
# Revoke All Tokens for User
# -----------------------------
def revoke_all_user_tokens(db: Session, user_id: UUID) -> None:
    """Useful for password change or security reset."""
    db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == user_id,
        models.RefreshToken.is_revoked == False,
    ).update({"is_revoked": True})
    db.commit()