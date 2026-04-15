"""
JWT token creation/decoding and password hashing utilities.

Uses bcrypt directly (no passlib) and python-jose for JWTs.
datetime.now(UTC) is used instead of the deprecated datetime.utcnow().
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import settings


# ---------------------------------------------------------------------------
# Password hashing — bcrypt (direct, no passlib wrapper)
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Returns a bcrypt hash of the supplied plain-text password."""
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Returns True if `plain_password` matches the stored hash."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


# Public alias kept for any router that imports pwd_context directly
class _PwdContextCompat:
    """Thin shim so existing code using pwd_context.hash() / .verify() keeps working."""
    def hash(self, secret: str) -> str:
        return hash_password(secret)

    def verify(self, secret: str, hashed: str) -> bool:
        return verify_password(secret, hashed)


pwd_context = _PwdContextCompat()


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(data: dict) -> str:
    """Creates a short-lived JWT access token (ACCESS_TOKEN_EXPIRE_MINUTES)."""
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Creates a long-lived JWT refresh token (REFRESH_TOKEN_EXPIRE_DAYS).
    Stored in Redis for revocation support.
    """
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodes and validates a JWT. Raises HTTP 401 on any failure."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
