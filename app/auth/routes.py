from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth import schemas, services, security
from app.auth.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


# -----------------------------
# Register User
# -----------------------------
@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = services.get_user_by_email(db, user_data.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    return services.create_user(db, user_data)


# -----------------------------
# Login User
# -----------------------------
@router.post("/login", response_model=schemas.Token)
def login_user(
    login_data: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    user = services.authenticate_user(db, login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = security.create_access_token(subject=str(user.id))
    refresh_token_str, expires_at = security.create_refresh_token()

    services.store_refresh_token(
        db,
        user_id=user.id,
        token=refresh_token_str,
        expires_at=expires_at,
    )

    return schemas.Token(
        access_token=access_token,
        refresh_token=refresh_token_str,
    )


# -----------------------------
# Refresh Access Token
# -----------------------------
@router.post("/refresh", response_model=schemas.Token)
def refresh_access_token(
    body: schemas.RefreshRequest,
    db: Session = Depends(get_db)
):
    record = services.get_valid_refresh_token(db, body.refresh_token)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user = services.get_user_by_id(db, record.user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Rotate: revoke old, issue new pair
    services.revoke_refresh_token(db, body.refresh_token)

    new_access_token = security.create_access_token(subject=str(user.id))
    new_refresh_token_str, new_expires_at = security.create_refresh_token()

    services.store_refresh_token(
        db,
        user_id=user.id,
        token=new_refresh_token_str,
        expires_at=new_expires_at,
    )

    return schemas.Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token_str,
    )


# -----------------------------
# Logout
# -----------------------------
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(
    body: schemas.LogoutRequest,
    db: Session = Depends(get_db)
):
    services.revoke_refresh_token(db, body.refresh_token)


# -----------------------------
# Get Current User
# — now uses reusable dependency from security.py
# -----------------------------
@router.get("/me", response_model=schemas.UserResponse)
def get_me(
    current_user: User = Depends(security.get_current_user),
):
    return current_user