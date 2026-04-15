"""Topic service."""
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.classroom import Enrollment, EnrollmentRole
from app.models.topic import Topic
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicUpdate


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
        raise HTTPException(status_code=403, detail="Only teachers can manage topics")


async def create_topic(db: AsyncSession, classroom_id: UUID, data: TopicCreate, current_user: User) -> Topic:
    await _verify_teacher(db, classroom_id, current_user.id, current_user.role)
    topic = Topic(classroom_id=classroom_id, title=data.title, order_index=data.order_index)
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return topic


async def list_topics(db: AsyncSession, classroom_id: UUID) -> List[Topic]:
    result = await db.execute(
        select(Topic)
        .where(Topic.classroom_id == classroom_id)
        .order_by(Topic.order_index, Topic.created_at)
    )
    return result.scalars().all()


async def update_topic(db: AsyncSession, topic_id: UUID, data: TopicUpdate, current_user: User) -> Topic:
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalars().first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    await _verify_teacher(db, topic.classroom_id, current_user.id, current_user.role)
    if data.title is not None:
        topic.title = data.title
    if data.order_index is not None:
        topic.order_index = data.order_index
    await db.commit()
    await db.refresh(topic)
    return topic


async def delete_topic(db: AsyncSession, topic_id: UUID, current_user: User) -> None:
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalars().first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    await _verify_teacher(db, topic.classroom_id, current_user.id, current_user.role)
    await db.delete(topic)
    await db.commit()
