"""Assignment + RubricCriterion Pydantic schemas."""

import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.assignment import SubmissionType, LatePolicy


class RubricLevelSchema(BaseModel):
    excellent: str = ""
    good: str = ""
    average: str = ""
    poor: str = ""


class RubricCriterionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    max_marks: int = Field(ge=1)
    order_index: int = Field(default=0, ge=0)
    levels: RubricLevelSchema = RubricLevelSchema()


class RubricCriterionResponse(BaseModel):
    id: uuid.UUID
    assignment_id: uuid.UUID
    name: str
    max_marks: int
    order_index: int
    levels: dict

    model_config = {"from_attributes": True}


class CreateAssignmentRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = ""
    deadline: datetime
    total_marks: int = Field(ge=1)
    submission_type: SubmissionType = SubmissionType.text
    max_drafts: int = Field(default=3, ge=1, le=10)
    late_policy: LatePolicy = LatePolicy.penalty
    penalty_per_day: Decimal = Decimal("0")
    rubric_criteria: list[RubricCriterionCreate] = Field(default_factory=list)


class UpdateAssignmentRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    deadline: datetime | None = None
    total_marks: int | None = None
    late_policy: LatePolicy | None = None
    penalty_per_day: Decimal | None = None


class AssignmentResponse(BaseModel):
    id: uuid.UUID
    classroom_id: uuid.UUID
    title: str
    description: str
    deadline: datetime
    total_marks: int
    submission_type: SubmissionType
    max_drafts: int
    late_policy: LatePolicy
    penalty_per_day: Decimal
    is_published: bool
    created_by: uuid.UUID
    created_at: datetime
    rubric_criteria: list[RubricCriterionResponse] = []

    model_config = {"from_attributes": True}
