"""
Submission routes.

POST  /assignments/{id}/drafts          — submit a draft (triggers AI feedback)
POST  /assignments/{id}/final           — submit final answer
GET   /assignments/{id}/submissions     — list all submissions (teacher)
GET   /assignments/{id}/my-submission   — get my submission history (student)
GET   /submissions/{id}                 — get a single submission
GET   /submissions/{id}/feedback        — get AI feedback for a draft
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai_feedback import AIFeedbackResponse
from app.schemas.submission import SubmissionCreate, SubmissionListItem, SubmissionResponse
from app.services import submission_service

router = APIRouter(tags=["Submissions"])


@router.post(
    "/assignments/{assignment_id}/drafts",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a draft (student only) — triggers AI feedback",
)
async def submit_draft(
    assignment_id: UUID,
    request: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a draft submission and queues a Celery task for LLM-powered
    rubric-aligned feedback.
    Returns 403 if the draft limit is reached.
    """
    return await submission_service.submit_draft(db, assignment_id, request, current_user)


@router.post(
    "/assignments/{assignment_id}/final",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit final answer (student only)",
)
async def submit_final(
    assignment_id: UUID,
    request: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates the one and only final submission for this assignment.
    Queues a plagiarism / similarity check in the background.
    Returns 409 if the student already submitted a final answer.
    """
    return await submission_service.submit_final(db, assignment_id, request, current_user)


@router.get(
    "/assignments/{assignment_id}/submissions",
    response_model=List[SubmissionListItem],
    summary="List all submissions for an assignment (teacher only)",
)
async def list_submissions(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all submissions (drafts + finals) for a given assignment.
    Only the teacher of that classroom can call this endpoint.
    """
    return await submission_service.list_submissions_for_assignment(db, assignment_id, current_user)


@router.get(
    "/assignments/{assignment_id}/my-submission",
    response_model=List[SubmissionResponse],
    summary="Get my full submission history for an assignment (student)",
)
async def get_my_submissions(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all drafts and the final submission for the authenticated student."""
    return await submission_service.get_my_submissions(db, assignment_id, current_user)


@router.get(
    "/submissions/{submission_id}",
    response_model=SubmissionResponse,
    summary="Get a single submission by ID",
)
async def get_submission(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns a single submission. Students can only see their own."""
    return await submission_service.get_submission(db, submission_id, current_user)


@router.get(
    "/submissions/{submission_id}/feedback",
    response_model=List[AIFeedbackResponse],
    summary="Get AI feedback for a draft submission",
)
async def get_ai_feedback(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the AI-generated rubric feedback for a draft.
    If feedback is not ready yet (worker still processing), returns an empty list.
    Returns 404 if the submission doesn't exist or doesn't belong to the caller.
    """
    return await submission_service.get_feedback(db, submission_id, current_user)
