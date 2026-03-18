from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(
    schemes=[settings.PASSWORD_HASH_SCHEME],
    deprecated="auto"
)

# -----------------------------
# OAuth2 scheme (for Swagger UI)
# -----------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


# -----------------------------
# Password Hashing
# -----------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# -----------------------------
# JWT Access Token
# -----------------------------
def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# -----------------------------
# Refresh Token (opaque string)
# -----------------------------
def create_refresh_token() -> tuple[str, datetime]:
    """
    Returns a (token_string, expires_at) tuple.
    Token is a cryptographically secure random string — NOT a JWT.
    Stored in DB and looked up on each refresh request.
    """
    token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return token, expires_at


# -----------------------------
# JWT Token Decoding
# -----------------------------
def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# -----------------------------
# Reusable: Get Current User
# -----------------------------
def get_current_user(
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    oauth_token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Reusable dependency — use as Depends(get_current_user) on any protected route.
    Accepts token from either HTTPBearer (Swagger lock icon) or OAuth2 header.
    """
    from app.auth import services  # local import to avoid circular dependency

    # Pick whichever scheme provided the token
    token = bearer.credentials if bearer else oauth_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ensure it's an access token, not a refresh token
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    user = services.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return user