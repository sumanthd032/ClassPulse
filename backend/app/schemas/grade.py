"""Grade Pydantic schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class CriterionGrade(BaseModel):
    criterion_id: uuid.UUID
    score: int = Field(ge=0)
    level: str = Field(pattern="^(excellent|good|average|poor)$")
    feedback: str = ""


class GradeSubmissionRequest(BaseModel):
    """Teacher grades a submission criterion by criterion."""
    grades: list[CriterionGrade]


class BulkFeedbackRequest(BaseModel):
    """Apply the same feedback to multiple students (Phase 3 full implementation)."""
    submission_ids: list[uuid.UUID]
    feedback: str


class GradeResponse(BaseModel):
    id: uuid.UUID
    submission_id: uuid.UUID
    criterion_id: uuid.UUID
    score: int
    level: str
    feedback: str
    graded_by: uuid.UUID
    is_released: bool
    created_at: datetime

    model_config = {"from_attributes": True}
