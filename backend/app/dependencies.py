"""Shared FastAPI dependency functions.

FastAPI's dependency injection system works like this:
  - A dependency is any callable that FastAPI calls before your route handler.
  - Use `Depends(some_function)` in route parameters.
  - FastAPI resolves the dependency graph automatically (async-aware).

Pattern here:
  get_db          → yields an async DB session (one per request, auto-committed/rolled-back)
  get_current_user → reads the JWT from Authorization header, returns the User ORM object
  require_teacher  → wraps get_current_user, raises 403 if not a teacher or admin
  require_admin    → wraps get_current_user, raises 403 if not an admin
"""

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedError, ForbiddenError

# HTTPBearer extracts the token from: Authorization: Bearer <token>
# auto_error=False means we handle the missing-token case ourselves (better error message).
bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    """Yield a DB session for the duration of one request.

    Using `async with` means:
      - session.commit() is called automatically on success
      - session.rollback() is called automatically on exception
      - session.close() is always called at the end
    """
    async with AsyncSessionLocal() as session:
        yield session


# Type alias — makes route signatures shorter
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DbSession,
) -> User:
    """Decode the JWT and return the corresponding User from the database.

    Steps:
      1. Extract Bearer token from Authorization header.
      2. Decode + validate the JWT (signature, expiry).
      3. Read user_id from the 'sub' claim.
      4. Fetch the User row from the DB (confirms account still exists/not deleted).
    """
    if credentials is None:
        raise UnauthorizedError("No authentication token provided.")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise UnauthorizedError("Invalid or expired token.")

    if payload.get("type") != "access":
        raise UnauthorizedError("Refresh tokens cannot be used for API calls.")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token is missing subject claim.")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("User account no longer exists.")

    return user


# Type alias for convenience
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_teacher(current_user: CurrentUser) -> User:
    """Raise 403 if the current user is not a teacher or admin."""
    if current_user.role not in (UserRole.teacher, UserRole.admin):
        raise ForbiddenError("Only teachers can perform this action.")
    return current_user


def require_admin(current_user: CurrentUser) -> User:
    """Raise 403 if the current user is not an admin."""
    if current_user.role != UserRole.admin:
        raise ForbiddenError("Only admins can perform this action.")
    return current_user


TeacherUser = Annotated[User, Depends(require_teacher)]
AdminUser = Annotated[User, Depends(require_admin)]
