"""
Dashboard routes — role-aware stats for the home page, plus grades list and analytics.

GET /me/dashboard              — returns stats appropriate for the caller's role
GET /me/grades                 — returns all released grades for the student
GET /me/grade-trends           — returns chronological grade data for charts
GET /classrooms/{id}/analytics — returns grade distribution for a classroom
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.grade import Grade
from app.models.assignment import Assignment
from app.models.classroom import Classroom
from app.services import dashboard_service

router = APIRouter(tags=["Dashboard"])


@router.get("/me/dashboard", summary="Get role-specific dashboard stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns aggregated statistics for the authenticated user's home page.

    **Teachers** get:
    - `active_classes`       — number of classrooms they manage
    - `total_assignments`    — assignments they have published
    - `pending_grades`       — final submissions awaiting grading

    **Students** get:
    - `enrolled_classes`     — classrooms they joined
    - `active_assignments`   — open assignments across all classes
    - `total_submissions`    — all drafts + finals they have submitted
    - `avg_score`            — average grade across released grades
    - `upcoming_deadlines`   — next 5 upcoming assignments not yet submitted
    - `recent_grades`        — last 5 released grades
    """
    if current_user.role == UserRole.teacher:
        return await dashboard_service.get_teacher_stats(db, current_user.id)
    return await dashboard_service.get_student_stats(db, current_user.id)


@router.get("/me/grades", summary="Get all released grades for the student")
async def get_my_grades(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all released grades for the authenticated student, newest first."""
    result = await db.execute(
        select(Grade, Assignment.title, Assignment.total_marks, Classroom.name.label("classroom_name"))
        .join(Assignment, Assignment.id == Grade.assignment_id)
        .join(Classroom, Classroom.id == Assignment.classroom_id)
        .where(
            Grade.student_id == current_user.id,
            Grade.is_released == True,  # noqa: E712
        )
        .order_by(Grade.graded_at.desc())
    )
    return [
        {
            "id": str(g.id),
            "assignment_id": str(g.assignment_id),
            "submission_id": str(g.submission_id),
            "assignment_title": at,
            "classroom_name": cn,
            "total_score": g.total_score,
            "total_marks": am,
            "teacher_comments": g.teacher_comments,
            "graded_at": g.graded_at.isoformat(),
        }
        for g, at, am, cn in result.all()
    ]


@router.get("/me/grade-trends", summary="Get grade trend data for charts (student)")
async def get_grade_trends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns chronological list of graded assignments for the student trend chart."""
    return await dashboard_service.get_grade_trends(db, current_user.id)


@router.get("/classrooms/{classroom_id}/analytics", summary="Get classroom grade analytics (teacher)")
async def get_classroom_analytics(
    classroom_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns grade distribution and class average for a classroom."""
    return await dashboard_service.get_classroom_analytics(db, classroom_id, current_user)
