"""Announcement (stream) service."""
from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.announcement import Announcement
from app.models.classroom import Enrollment, EnrollmentRole
from app.models.comment import Comment
from app.models.user import User
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate


async def _verify_enrolled(db: AsyncSession, classroom_id: UUID, user_id: UUID) -> None:
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.classroom_id == classroom_id,
            Enrollment.user_id == user_id,
        )
    )
    if not result.scalars().first():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this classroom")


async def _verify_teacher(db: AsyncSession, classroom_id: UUID, user_id: UUID, role: str) -> None:
    if role == "admin":
        return
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.classroom_id == classroom_id,
            Enrollment.user_id == user_id,
            Enrollment.role == EnrollmentRole.co_teacher,
        )
    )
    if not result.scalars().first():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can post announcements")


async def create_announcement(
    db: AsyncSession, classroom_id: UUID, data: AnnouncementCreate, current_user: User
) -> dict:
    await _verify_teacher(db, classroom_id, current_user.id, current_user.role)
    ann = Announcement(
        classroom_id=classroom_id,
        author_id=current_user.id,
        title=data.title,
        content=data.content,
        pinned=data.pinned,
        attachment_urls=[],
    )
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return await _enrich(db, ann)


async def list_announcements(
    db: AsyncSession, classroom_id: UUID, current_user: User, skip: int = 0, limit: int = 20
) -> List[dict]:
    await _verify_enrolled(db, classroom_id, current_user.id)
    result = await db.execute(
        select(Announcement)
        .where(Announcement.classroom_id == classroom_id)
        .order_by(Announcement.pinned.desc(), Announcement.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    anns = result.scalars().all()
    return [await _enrich(db, a) for a in anns]


async def update_announcement(
    db: AsyncSession, announcement_id: UUID, data: AnnouncementUpdate, current_user: User
) -> dict:
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    ann = result.scalars().first()
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    await _verify_teacher(db, ann.classroom_id, current_user.id, current_user.role)
    if data.title is not None:
        ann.title = data.title
    if data.content is not None:
        ann.content = data.content
    if data.pinned is not None:
        ann.pinned = data.pinned
    await db.commit()
    await db.refresh(ann)
    return await _enrich(db, ann)


async def delete_announcement(db: AsyncSession, announcement_id: UUID, current_user: User) -> None:
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    ann = result.scalars().first()
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    await _verify_teacher(db, ann.classroom_id, current_user.id, current_user.role)
    await db.delete(ann)
    await db.commit()


async def _enrich(db: AsyncSession, ann: Announcement) -> dict:
    author_result = await db.execute(select(User).where(User.id == ann.author_id))
    author = author_result.scalars().first()
    count_result = await db.execute(
        select(func.count(Comment.id)).where(Comment.announcement_id == ann.id)
    )
    comment_count = count_result.scalar() or 0
    return {
        "id": ann.id,
        "classroom_id": ann.classroom_id,
        "author_id": ann.author_id,
        "author": {
            "id": author.id,
            "full_name": author.full_name,
            "avatar_url": author.avatar_url,
            "role": author.role,
        } if author else None,
        "title": ann.title,
        "content": ann.content,
        "pinned": ann.pinned,
        "attachment_urls": ann.attachment_urls or [],
        "comment_count": comment_count,
        "created_at": ann.created_at,
        "updated_at": ann.updated_at,
    }
