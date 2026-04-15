from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TopicCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    order_index: int = 0


class TopicUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    order_index: Optional[int] = None


class TopicResponse(BaseModel):
    id: UUID
    classroom_id: UUID
    title: str
    order_index: int
    created_at: datetime

    model_config = {"from_attributes": True}
