"""Topic routes."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate
from app.services import topic_service

router = APIRouter(tags=["Topics"])


@router.post(
    "/classrooms/{classroom_id}/topics",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_topic(
    classroom_id: UUID,
    data: TopicCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await topic_service.create_topic(db, classroom_id, data, current_user)


@router.get("/classrooms/{classroom_id}/topics", response_model=List[TopicResponse])
async def list_topics(
    classroom_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await topic_service.list_topics(db, classroom_id)


@router.patch("/topics/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: UUID,
    data: TopicUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await topic_service.update_topic(db, topic_id, data, current_user)


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await topic_service.delete_topic(db, topic_id, current_user)
