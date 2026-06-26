"""Pydantic schemas for assignment and rubric endpoints."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.assignment import LatePolicy, SubmissionType


# ---------------------------------------------------------------------------
# Rubric
# ---------------------------------------------------------------------------

class RubricCriteriaCreate(BaseModel):
    """A single rubric criterion supplied at assignment creation time."""
    name: str = Field(..., max_length=100)
    max_marks: int = Field(..., ge=1)
    # Expected format: {"excellent": "...", "good": "...", "average": "...", "poor": "..."}
    levels: Dict[str, str]


class RubricCriteriaResponse(BaseModel):
    id: UUID
    name: str
    max_marks: int
    order_index: int
    levels: Dict[str, Any]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------

class AssignmentCreate(BaseModel):
    """
    Full assignment payload including an embedded rubric.
    The sum of `criteria[*].max_marks` must equal `total_marks` — enforced in
    the service layer to provide a descriptive error.
    """
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    deadline: datetime
    total_marks: int = Field(..., ge=1)
    submission_type: SubmissionType = SubmissionType.text
    max_drafts: int = Field(3, ge=1, le=10)
    late_policy: LatePolicy = LatePolicy.penalty
    penalty_per_day: Optional[float] = Field(None, ge=0, le=100)
    is_published: bool = True
    criteria: List[RubricCriteriaCreate] = Field(..., min_length=1)


class AssignmentUpdate(BaseModel):
    """Partial update for a draft/unpublished assignment."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    is_published: Optional[bool] = None


class AssignmentResponse(BaseModel):
    id: UUID
    classroom_id: UUID
    title: str
    description: Optional[str]
    deadline: datetime
    total_marks: int
    submission_type: SubmissionType
    max_drafts: int
    late_policy: LatePolicy
    penalty_per_day: Optional[float]
    is_published: bool
    created_by: UUID
    criteria: List[RubricCriteriaResponse] = []

    model_config = {"from_attributes": True}
