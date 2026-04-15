"""Pydantic schemas for AI feedback responses."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AIFeedbackResponse(BaseModel):
    """
    One AI feedback record per rubric criterion per submission.
    Returned when a student requests feedback on their draft.
    """
    id: UUID
    submission_id: UUID
    criterion_id: UUID
    criterion_name: Optional[str] = None   # Human-readable name from RubricCriteria
    criterion_max_marks: Optional[int] = None
    estimated_score: int
    feedback_text: str          # "Strengths: ...\nImprovements: ..."
    suggested_level: str        # "excellent" | "good" | "average" | "poor"
    generated_at: datetime

    model_config = {"from_attributes": True}
