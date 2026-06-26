"""
Grading routes.

GET    /assignments/{id}/grading-queue  — list final submissions needing grades
POST   /submissions/{id}/grade          — grade a submission (upsert)
GET    /submissions/{id}/grade          — get a grade (student sees own; teacher sees all)
GET    /assignments/{id}/gradebook      — full student × grade matrix (teacher only)
GET    /assignments/{id}/gradebook/pdf  — download PDF gradebook (teacher only)
"""
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.grade import GradeCreate, GradeResponse
from app.services import grading_service, gradebook_service

router = APIRouter(tags=["Grading"])


@router.get(
    "/assignments/{assignment_id}/grading-queue",
    response_model=List[Any],
    summary="List final submissions awaiting grading (teacher only)",
)
async def get_grading_queue(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all final submissions for this assignment that have not yet
    been graded.  Only the teacher of that classroom can call this.
    """
    return await grading_service.get_grading_queue(db, assignment_id, current_user)


@router.post(
    "/submissions/{submission_id}/grade",
    response_model=GradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grade a final submission (teacher only)",
)
async def grade_submission(
    submission_id: UUID,
    request: GradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates or updates the grade for a final submission (upsert).
    If `is_released=True`, the student receives a real-time WebSocket notification.
    Returns 400 if called on a draft submission.
    Returns 403 if the caller is not a teacher in that classroom.
    """
    return await grading_service.grade_submission(db, submission_id, request, current_user)


@router.get(
    "/submissions/{submission_id}/grade",
    response_model=GradeResponse,
    summary="Get the grade for a submission",
)
async def get_grade(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the grade for a submission.
    - Teachers can always see it.
    - Students only see it when `is_released=True`.
    Returns 404 if no grade exists yet.
    """
    return await grading_service.get_grade(db, submission_id, current_user)


@router.post(
    "/assignments/{assignment_id}/grades/release-all",
    summary="Release all graded submissions for an assignment (teacher only)",
)
async def release_all_grades(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk-releases all grades for an assignment and pushes WebSocket notifications."""
    return await grading_service.release_all_grades(db, assignment_id, current_user)


@router.get(
    "/assignments/{assignment_id}/gradebook",
    response_model=List[Any],
    summary="Full gradebook — all students with grade status (teacher only)",
)
async def get_gradebook(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns one row per enrolled student showing submission status,
    score, percentage, letter grade, and release status.
    """
    return await gradebook_service.get_gradebook(db, assignment_id, current_user)


@router.get(
    "/assignments/{assignment_id}/gradebook/pdf",
    summary="Download PDF gradebook (teacher only)",
)
async def download_gradebook_pdf(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates and streams a formatted PDF gradebook for the assignment.
    Suitable for official documentation and record-keeping.
    """
    pdf_bytes = await gradebook_service.generate_pdf(db, assignment_id, current_user)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=gradebook-{assignment_id}.pdf",
            "Content-Length": str(len(pdf_bytes)),
        },
    )
