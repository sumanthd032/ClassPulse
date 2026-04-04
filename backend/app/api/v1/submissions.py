"""Submission endpoints: submit-draft, submit-final, my-submissions, feedback."""

import uuid
from fastapi import APIRouter

from app.dependencies import DbSession, CurrentUser, TeacherUser
from app.schemas.submission import SubmitDraftRequest, SubmitFinalRequest, SubmissionResponse
from app.services import submission_service
from app.workers.tasks.ai_feedback import generate_ai_feedback

router = APIRouter()


@router.post("/assignments/{assignment_id}/submit-draft", response_model=SubmissionResponse, status_code=201)
async def submit_draft(
    assignment_id: uuid.UUID,
    body: SubmitDraftRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Submit a draft and trigger AI feedback generation.

    What happens after this returns:
      1. Submission row is created in DB (draft_number incremented).
      2. Celery task `generate_ai_feedback` is enqueued asynchronously.
      3. API returns 201 immediately — student sees "Feedback generating..."
      4. Worker calls LLM, stores feedback, publishes Redis event.
      5. (Phase 2) WebSocket pushes "feedback_ready" to student's browser.

    Why .delay() not .apply_async()?
      .delay() is shorthand for .apply_async(args=[...]) with no extra options.
      It's cleaner for simple cases.
    """
    submission = await submission_service.submit_draft(
        db, current_user, assignment_id, body.content, body.file_url
    )
    # Queue the AI feedback task — non-blocking, returns immediately
    generate_ai_feedback.delay(str(submission.id))

    subs = await submission_service.get_my_submissions(db, current_user.id, assignment_id)
    return next(s for s in subs if s.id == submission.id)


@router.post("/assignments/{assignment_id}/submit-final", response_model=SubmissionResponse, status_code=201)
async def submit_final(
    assignment_id: uuid.UUID,
    body: SubmitFinalRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Lock in the final submission.
    - Immutable after this point (no more drafts or edits allowed).
    - Phase 3: triggers similarity detection task.
    """
    submission = await submission_service.submit_final(
        db, current_user, assignment_id, body.content, body.file_url
    )
    # Phase 3: detect_similarity.delay(str(assignment_id))
    subs = await submission_service.get_my_submissions(db, current_user.id, assignment_id)
    return next(s for s in subs if s.id == submission.id)


@router.get("/assignments/{assignment_id}/my-submissions", response_model=list[SubmissionResponse])
async def my_submissions(assignment_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    """Return all drafts + final for the current student, with AI feedback attached."""
    return await submission_service.get_my_submissions(db, current_user.id, assignment_id)


@router.get("/assignments/{assignment_id}/submissions", response_model=list[SubmissionResponse])
async def all_submissions(assignment_id: uuid.UUID, db: DbSession, current_user: TeacherUser):
    """Return all final submissions for teacher's grading view."""
    return await submission_service.get_all_submissions_for_assignment(db, assignment_id)
