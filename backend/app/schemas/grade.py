"""Pydantic schemas for grading endpoints."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CriterionScoreCreate(BaseModel):
    criterion_id: UUID
    score: int = Field(..., ge=0)
    comment: Optional[str] = None


class CriterionScoreResponse(BaseModel):
    id: UUID
    criterion_id: UUID
    score: int
    comment: Optional[str] = None

    model_config = {"from_attributes": True}


class GradeCreate(BaseModel):
    """What the teacher sends when grading a final submission."""
    total_score: int = Field(..., ge=0)
    teacher_comments: Optional[str] = None
    # Grades are NEVER auto-released; teacher must explicitly set True
    is_released: bool = False
    criterion_scores: Optional[List[CriterionScoreCreate]] = None


class GradeResponse(BaseModel):
    """Grade detail returned to the frontend."""
    id: UUID
    submission_id: UUID
    assignment_id: UUID
    student_id: UUID
    grader_id: UUID
    total_score: int
    teacher_comments: Optional[str] = None
    is_released: bool
    graded_at: datetime
    criterion_grades: List[CriterionScoreResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
