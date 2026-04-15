"""Comment routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.comment import CommentCreate
from app.services import comment_service

router = APIRouter(tags=["Comments"])


@router.post("/announcements/{announcement_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_announcement_comment(
    announcement_id: UUID,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await comment_service.add_announcement_comment(db, announcement_id, data, current_user)


@router.get("/announcements/{announcement_id}/comments")
async def list_announcement_comments(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await comment_service.list_announcement_comments(db, announcement_id, current_user)


@router.post("/assignments/{assignment_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_assignment_comment(
    assignment_id: UUID,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await comment_service.add_assignment_comment(db, assignment_id, data, current_user)


@router.get("/assignments/{assignment_id}/comments")
async def list_assignment_comments(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await comment_service.list_assignment_comments(db, assignment_id, current_user)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await comment_service.delete_comment(db, comment_id, current_user)
