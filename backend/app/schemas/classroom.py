"""Classroom + Enrollment Pydantic schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.classroom import EnrollmentRole


class ClassroomSettings(BaseModel):
    max_drafts: int = Field(default=3, ge=1, le=10)
    late_policy: str = Field(default="penalty", pattern="^(block|penalty|allow)$")
    ai_feedback: bool = True


class CreateClassroomRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    subject_code: str = Field(min_length=2, max_length=20)
    section: str = Field(min_length=1, max_length=10)
    semester: str = Field(min_length=1, max_length=10)
    settings: ClassroomSettings = ClassroomSettings()


class UpdateClassroomSettingsRequest(BaseModel):
    settings: ClassroomSettings


class JoinClassroomRequest(BaseModel):
    join_code: str = Field(min_length=6, max_length=6)


class ClassroomResponse(BaseModel):
    id: uuid.UUID
    name: str
    subject_code: str
    section: str
    semester: str
    join_code: str
    created_by: uuid.UUID
    settings: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class EnrollmentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    classroom_id: uuid.UUID
    role: EnrollmentRole
    joined_at: datetime

    model_config = {"from_attributes": True}
