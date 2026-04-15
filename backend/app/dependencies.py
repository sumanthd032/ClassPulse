"""
FastAPI dependency-injection helpers.

Provides:
  - get_current_user  — decodes the Bearer JWT and returns the User model
  - require_teacher   — 403 guard for teacher/admin-only routes
  - require_student   — 403 guard for student-only routes
  - require_admin     — 403 guard for admin-only routes
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user import User, UserRole
from app.utils.security import decode_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decodes the JWT Bearer token, validates it, and returns the matching User
    row from the database.

    Raises HTTP 401 if the token is missing, expired, tampered with, or the
    user no longer exists.
    """
    payload = decode_token(credentials.credentials)

    email: str | None = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing email claim",
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
        )
    return user


async def require_teacher(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Raises HTTP 403 if the caller is not a teacher or admin.
    Use as a route dependency: `current_user: User = Depends(require_teacher)`.
    """
    if current_user.role not in (UserRole.teacher, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can perform this action",
        )
    return current_user


async def require_student(
    current_user: User = Depends(get_current_user),
) -> User:
    """Raises HTTP 403 if the caller is not a student."""
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can perform this action",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Raises HTTP 403 if the caller is not an admin."""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action",
        )
    return current_user
