"""Announcement (stream) routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate
from app.services import announcement_service

router = APIRouter(tags=["Announcements"])


@router.post(
    "/classrooms/{classroom_id}/announcements",
    status_code=status.HTTP_201_CREATED,
    summary="Post an announcement to the stream (teacher only)",
)
async def create_announcement(
    classroom_id: UUID,
    data: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await announcement_service.create_announcement(db, classroom_id, data, current_user)


@router.get(
    "/classrooms/{classroom_id}/announcements",
    summary="List announcements for a classroom",
)
async def list_announcements(
    classroom_id: UUID,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await announcement_service.list_announcements(db, classroom_id, current_user, skip, limit)


@router.patch(
    "/announcements/{announcement_id}",
    summary="Edit an announcement (teacher only)",
)
async def update_announcement(
    announcement_id: UUID,
    data: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await announcement_service.update_announcement(db, announcement_id, data, current_user)


@router.delete(
    "/announcements/{announcement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an announcement (teacher only)",
)
async def delete_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await announcement_service.delete_announcement(db, announcement_id, current_user)
