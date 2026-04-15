"""
Authentication routes.

POST /register   — create a new account
POST /login      — authenticate and receive JWT tokens
POST /refresh    — rotate tokens using a valid refresh token
POST /logout     — invalidate the current session (revoke refresh token)
GET  /me         — return the authenticated user's profile
"""
from fastapi import APIRouter, Body, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, ProfileUpdateRequest, RegisterRequest, TokenResponse, UserResponse
from app.services import auth_service
from app.utils.redis_client import get_redis
from app.utils.security import create_access_token, create_refresh_token, decode_token, pwd_context

router = APIRouter(tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user.
    - Email must be unique (409 if already taken).
    - Password is bcrypt-hashed before storage.
    """
    return await auth_service.register_user(db, request)


@router.post("/login", response_model=TokenResponse, summary="Authenticate and get JWT tokens")
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Validates email + password and returns:
    - `access_token` — short-lived (15 min default)
    - `refresh_token` — long-lived (7 days default), stored in Redis for revocation
    """
    user = await auth_service.authenticate_user(db, request)

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )

    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    await redis.setex(f"refresh:{user.id}", ttl, refresh_token)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=TokenResponse, summary="Rotate tokens using a refresh token")
async def refresh_tokens(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Validates the refresh token against Redis, then issues a fresh pair.
    The old refresh token is replaced (token rotation prevents replay attacks).
    Returns 401 if the token is expired, revoked, or tampered with.
    """
    payload = decode_token(refresh_token)
    user_id = payload.get("sub")
    email = payload.get("email")

    # Verify the token matches what we stored (revocation check)
    stored = await redis.get(f"refresh:{user_id}")
    if not stored or stored != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or has been revoked",
        )

    user = await auth_service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    new_refresh = create_refresh_token(data={"sub": str(user.id), "email": user.email})

    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    await redis.setex(f"refresh:{user.id}", ttl, new_refresh)

    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate the current session",
)
async def logout(
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    """
    Deletes the refresh token from Redis.
    The client must discard both tokens locally after calling this endpoint.
    """
    await redis.delete(f"refresh:{current_user.id}")


@router.get("/me", response_model=UserResponse, summary="Get authenticated user profile")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Returns the profile of the currently authenticated user (no password hash)."""
    return current_user


@router.patch("/me", response_model=UserResponse, summary="Update authenticated user profile")
async def update_my_profile(
    request: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially updates the caller's profile.
    - `full_name`  — display name
    - `avatar_url` — public URL for the avatar image
    - `password`   — new password (min 8 chars), will be re-hashed
    """
    if request.full_name is not None:
        current_user.full_name = request.full_name
    if request.avatar_url is not None:
        current_user.avatar_url = request.avatar_url
    if request.password is not None:
        current_user.password_hash = pwd_context.hash(request.password)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
