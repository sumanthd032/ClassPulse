"""
Admin routes — HOD/Admin-only platform analytics.

GET  /admin/stats       — platform-wide counts
GET  /admin/users       — paginated user list
GET  /admin/classrooms  — paginated classroom list with enrollment counts
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", summary="Platform-wide statistics (admin only)")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Returns total users, classrooms, assignments, submissions, grades."""
    return await admin_service.get_platform_stats(db)


@router.get("/users", summary="Paginated user list (admin only)")
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role: student | teacher | admin"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Returns all users, optionally filtered by role. Paginated."""
    return await admin_service.list_users(db, role=role, limit=limit, offset=offset)


@router.get("/classrooms", summary="All classrooms with enrollment counts (admin only)")
async def list_classrooms(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Returns all classrooms with student enrollment count."""
    return await admin_service.list_all_classrooms(db, limit=limit, offset=offset)
