from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1)
    pinned: bool = False


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[str] = None
    pinned: Optional[bool] = None


class AnnouncementAuthor(BaseModel):
    id: UUID
    full_name: str
    avatar_url: Optional[str] = None
    role: str

    model_config = {"from_attributes": True}


class AnnouncementResponse(BaseModel):
    id: UUID
    classroom_id: UUID
    author_id: UUID
    author: Optional[AnnouncementAuthor] = None
    title: str
    content: str
    pinned: bool
    attachment_urls: List[str] = []
    comment_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
