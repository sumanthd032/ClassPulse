"""Grading endpoints."""

import uuid
from fastapi import APIRouter

from app.dependencies import DbSession, TeacherUser
from app.schemas.grade import GradeSubmissionRequest, GradeResponse
from app.services import grading_service

router = APIRouter()


@router.post("/submissions/{submission_id}/grade", response_model=list[GradeResponse])
async def grade_submission(
    submission_id: uuid.UUID,
    body: GradeSubmissionRequest,
    db: DbSession,
    current_user: TeacherUser,
):
    """
    Rubric click-scoring: teacher assigns score + level per criterion.
    The UI shows criteria as clickable cards — Excellent/Good/Average/Poor.
    Each click maps to a predefined score based on max_marks and level proportions.
    AI-suggested grades are pre-filled on the frontend; teacher approves or adjusts.
    """
    grades_data = [g.model_dump() for g in body.grades]
    return await grading_service.grade_submission(db, current_user, submission_id, grades_data)


@router.post("/assignments/{assignment_id}/release-grades")
async def release_grades(assignment_id: uuid.UUID, db: DbSession, current_user: TeacherUser):
    """
    Release grades for all students in an assignment simultaneously.
    Before release, grades are only visible to the teacher.
    Phase 2: broadcasts grade_released WebSocket event to each student.
    """
    count = await grading_service.release_grades(db, current_user, assignment_id)
    return {"released": count, "message": f"{count} grade(s) released to students."}
