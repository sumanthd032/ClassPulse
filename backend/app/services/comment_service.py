"""Comment service."""
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.announcement import Announcement
from app.models.assignment import Assignment
from app.models.classroom import Enrollment
from app.models.comment import Comment
from app.models.user import User
from app.schemas.comment import CommentCreate


async def _verify_enrolled(db: AsyncSession, classroom_id: UUID, user_id: UUID) -> None:
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.classroom_id == classroom_id,
            Enrollment.user_id == user_id,
        )
    )
    if not result.scalars().first():
        raise HTTPException(status_code=403, detail="Not enrolled in this classroom")


async def add_announcement_comment(
    db: AsyncSession, announcement_id: UUID, data: CommentCreate, current_user: User
) -> dict:
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    ann = result.scalars().first()
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    await _verify_enrolled(db, ann.classroom_id, current_user.id)
    comment = Comment(author_id=current_user.id, announcement_id=announcement_id, content=data.content)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return await _enrich(db, comment)


async def list_announcement_comments(
    db: AsyncSession, announcement_id: UUID, current_user: User
) -> List[dict]:
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    ann = result.scalars().first()
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    await _verify_enrolled(db, ann.classroom_id, current_user.id)
    c_result = await db.execute(
        select(Comment)
        .where(Comment.announcement_id == announcement_id)
        .order_by(Comment.created_at)
    )
    return [await _enrich(db, c) for c in c_result.scalars().all()]


async def add_assignment_comment(
    db: AsyncSession, assignment_id: UUID, data: CommentCreate, current_user: User
) -> dict:
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assign = result.scalars().first()
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await _verify_enrolled(db, assign.classroom_id, current_user.id)
    comment = Comment(author_id=current_user.id, assignment_id=assignment_id, content=data.content)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return await _enrich(db, comment)


async def list_assignment_comments(
    db: AsyncSession, assignment_id: UUID, current_user: User
) -> List[dict]:
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assign = result.scalars().first()
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await _verify_enrolled(db, assign.classroom_id, current_user.id)
    c_result = await db.execute(
        select(Comment)
        .where(Comment.assignment_id == assignment_id)
        .order_by(Comment.created_at)
    )
    return [await _enrich(db, c) for c in c_result.scalars().all()]


async def delete_comment(db: AsyncSession, comment_id: UUID, current_user: User) -> None:
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if str(comment.author_id) != str(current_user.id) and current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Cannot delete this comment")
    await db.delete(comment)
    await db.commit()


async def _enrich(db: AsyncSession, comment: Comment) -> dict:
    author_result = await db.execute(select(User).where(User.id == comment.author_id))
    author = author_result.scalars().first()
    return {
        "id": comment.id,
        "author_id": comment.author_id,
        "author": {
            "id": author.id,
            "full_name": author.full_name,
            "avatar_url": author.avatar_url,
            "role": author.role,
        } if author else None,
        "content": comment.content,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }
