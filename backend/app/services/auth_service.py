"""
Authentication service — handles user registration and credential verification.
"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.utils.security import hash_password, verify_password


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Returns the User matching the given email, or None if not found."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    """
    Registers a new user account.

    Steps:
      1. Check email uniqueness (409 if taken).
      2. Hash the password with bcrypt.
      3. Persist the new User row.

    Returns the newly created User.
    """
    if await get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    new_user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def authenticate_user(db: AsyncSession, data: LoginRequest) -> User:
    """
    Verifies email and password.
    Returns the User on success, raises HTTP 401 on failure.

    Note: we use the same error message for both 'user not found' and 'wrong
    password' to prevent user-enumeration attacks.
    """
    user = await get_user_by_email(db, data.email)

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return user
