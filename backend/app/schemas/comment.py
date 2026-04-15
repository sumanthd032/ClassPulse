from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentAuthor(BaseModel):
    id: UUID
    full_name: str
    avatar_url: Optional[str] = None
    role: str

    model_config = {"from_attributes": True}


class CommentResponse(BaseModel):
    id: UUID
    author_id: UUID
    author: Optional[CommentAuthor] = None
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
