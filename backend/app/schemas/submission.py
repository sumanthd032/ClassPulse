"""Pydantic schemas for submission endpoints."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SubmissionCreate(BaseModel):
    """What the student sends when writing or uploading an answer."""
    content: Optional[str] = None       # Plain-text or Markdown answer
    file_url: Optional[str] = None      # URL if the student uploads a file


class SubmissionResponse(BaseModel):
    """Submission detail returned to the frontend."""
    id: UUID
    assignment_id: UUID
    student_id: UUID
    content: Optional[str]
    file_url: Optional[str]
    is_final: bool
    draft_number: int
    is_late: bool
    similarity_score: Optional[float]   # Populated after plagiarism check
    similarity_flagged: bool
    submitted_at: datetime

    model_config = {"from_attributes": True}


class SubmissionListItem(BaseModel):
    """Lightweight submission entry for list views (e.g., teacher's grading queue)."""
    id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    content: Optional[str] = None
    is_final: bool
    draft_number: int
    is_late: bool
    similarity_score: Optional[float] = None
    similarity_flagged: bool
    submitted_at: datetime

    model_config = {"from_attributes": True}
