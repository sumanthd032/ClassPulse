from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MaterialCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    material_type: str = "link"
    url: Optional[str] = None
    description: Optional[str] = None
    topic_id: Optional[UUID] = None
    file_id: Optional[UUID] = None


class MaterialResponse(BaseModel):
    id: UUID
    classroom_id: UUID
    topic_id: Optional[UUID] = None
    title: str
    material_type: str
    url: Optional[str] = None
    description: Optional[str] = None
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
