"""Auth endpoints: register, login, refresh, me.

Flow:
  POST /auth/register  → hash password → create User → return tokens
  POST /auth/login     → verify password → return tokens
  POST /auth/refresh   → decode refresh token → return new access token
  GET  /auth/me        → return current user (needs valid access token)
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter

from app.dependencies import DbSession, CurrentUser
from app.models.user import User
from app.schemas.user import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, UserResponse
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token, JWTError
)
from app.core.exceptions import ConflictError, UnauthorizedError

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: DbSession):
    """
    Create a new user account.
    - Email must be unique (DB unique constraint + explicit 409 response).
    - Password is bcrypt-hashed before storage. The plain text is never persisted.
    - Returns JWT tokens immediately — no separate login step required.
    """
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise ConflictError("An account with this email already exists.")

    return _build_token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: DbSession):
    """
    Authenticate with email + password.
    - We always call verify_password even if the user doesn't exist.
      This prevents timing attacks that could reveal whether an email is registered.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Constant-time check: always verify even if user is None (dummy hash fallback)
    dummy_hash = "$2b$12$dummyhashfortimingprotectiononly.....AAAAAAAAA"
    stored_hash = user.password_hash if user else dummy_hash
    if not verify_password(body.password, stored_hash) or user is None:
        raise UnauthorizedError("Invalid email or password.")

    return _build_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DbSession):
    """
    Exchange a refresh token for a new access token.
    The refresh token is validated (signature + expiry) but not stored server-side
    (stateless refresh). If you need token revocation, store refresh tokens in Redis.
    """
    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise UnauthorizedError("Invalid or expired refresh token.")

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Not a refresh token.")

    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User no longer exists.")

    return _build_token_response(user)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    """Return the currently authenticated user's profile."""
    return current_user


def _build_token_response(user: User) -> TokenResponse:
    """Helper — construct a TokenResponse from a User ORM object."""
    user_id = str(user.id)
    return TokenResponse(
        access_token=create_access_token(user_id, user.role.value),
        refresh_token=create_refresh_token(user_id),
        user=UserResponse.model_validate(user),
    )
