"""Submission + AIFeedback Pydantic schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel


class SubmitDraftRequest(BaseModel):
    content: str
    file_url: str | None = None


class SubmitFinalRequest(BaseModel):
    content: str
    file_url: str | None = None


class AIFeedbackResponse(BaseModel):
    id: uuid.UUID
    criterion_id: uuid.UUID
    estimated_score: int
    feedback_text: str
    generated_at: datetime

    model_config = {"from_attributes": True}


class SubmissionResponse(BaseModel):
    id: uuid.UUID
    assignment_id: uuid.UUID
    student_id: uuid.UUID
    content: str
    file_url: str | None
    is_final: bool
    draft_number: int
    is_late: bool
    submitted_at: datetime
    ai_feedback: list[AIFeedbackResponse] = []

    model_config = {"from_attributes": True}
