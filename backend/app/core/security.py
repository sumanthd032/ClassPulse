"""JWT creation/verification and bcrypt password hashing."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# bcrypt is the hashing algorithm — it's intentionally slow to resist brute-force attacks.
# passlib wraps it with a clean API and handles salt generation automatically.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if the plain password matches the stored hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, role: str) -> str:
    """
    Create a short-lived JWT access token (15 min by default).
    The token payload (called 'claims') carries:
      - sub: the user's UUID (standard JWT 'subject' claim)
      - role: the user's role so endpoints can check permissions without a DB hit
      - exp: expiry timestamp (jose validates this automatically)
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user_id, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    """
    Create a long-lived refresh token (7 days).
    Refresh tokens only carry the sub — they cannot be used as access tokens.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": user_id, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT. Raises JWTError if:
      - signature is invalid (tampered token)
      - token is expired
      - token is malformed
    Returns the raw payload dict on success.
    """
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


# Re-export JWTError so callers don't need to import jose directly.
__all__ = [
    "hash_password", "verify_password",
    "create_access_token", "create_refresh_token",
    "decode_token", "JWTError",
]
