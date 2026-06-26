"""Pydantic schemas for classroom and enrollment endpoints."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ClassroomCreate(BaseModel):
    """Payload to create a new classroom."""
    name: str = Field(..., min_length=2, max_length=100)
    subject_code: str = Field(..., max_length=20)
    section: str = Field(..., max_length=10)
    semester: str = Field(..., max_length=10)


class ClassroomJoin(BaseModel):
    """Payload for a student to join a classroom."""
    join_code: str = Field(..., min_length=6, max_length=6)


class ClassroomUpdate(BaseModel):
    """Partial update for classroom metadata and settings."""
    name: Optional[str] = Field(None, max_length=100)
    # Settings embedded in JSONB; all fields are optional (merge-patch style)
    max_drafts: Optional[int] = Field(None, ge=1, le=10)
    late_policy: Optional[str] = None
    ai_feedback: Optional[bool] = None


class ClassroomResponse(BaseModel):
    """Full classroom detail sent to clients."""
    id: UUID
    name: str
    subject_code: str
    section: str
    semester: str
    join_code: str
    created_by: UUID
    settings: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class EnrollmentResponse(BaseModel):
    """Enrollment record with nested classroom detail — used on dashboard lists."""
    classroom_id: UUID
    role: str
    joined_at: datetime
    classroom: ClassroomResponse

    model_config = {"from_attributes": True}


class StudentListItem(BaseModel):
    """Student entry in a teacher's classroom roster."""
    user_id: UUID
    full_name: str
    email: str
    joined_at: datetime

    model_config = {"from_attributes": True}
