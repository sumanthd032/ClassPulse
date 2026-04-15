"""
Dashboard service — aggregates statistics for the home page.

Separate query paths for teachers and students keep the SQL simple and fast.
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.assignment import Assignment
from app.models.classroom import Classroom, Enrollment, EnrollmentRole
from app.models.grade import Grade
from app.models.submission import Submission


async def get_student_stats(db: AsyncSession, student_id: UUID) -> dict:
    """
    Returns a stats snapshot for the student dashboard.

    Fields:
      - enrolled_classes     number of classrooms joined
      - active_assignments   total assignments across enrolled classrooms
      - total_submissions    all drafts + finals ever submitted
      - avg_score            average of released grades (None if none yet)
    """
    # Enrolled class count
    enroll_result = await db.execute(
        select(func.count(Enrollment.id)).where(
            Enrollment.user_id == student_id,
            Enrollment.role == EnrollmentRole.student,
        )
    )
    enrolled_classes = enroll_result.scalar() or 0

    # Total published assignments across enrolled classrooms
    assign_result = await db.execute(
        select(func.count(Assignment.id))
        .join(Enrollment, Enrollment.classroom_id == Assignment.classroom_id)
        .where(
            Enrollment.user_id == student_id,
            Enrollment.role == EnrollmentRole.student,
            Assignment.is_published == True,  # noqa: E712
        )
    )
    active_assignments = assign_result.scalar() or 0

    # Total submissions (drafts + finals)
    sub_result = await db.execute(
        select(func.count(Submission.id)).where(Submission.student_id == student_id)
    )
    total_submissions = sub_result.scalar() or 0

    # Average released grade
    avg_result = await db.execute(
        select(func.avg(Grade.total_score)).where(
            Grade.student_id == student_id,
            Grade.is_released == True,  # noqa: E712
        )
    )
    avg_score_raw = avg_result.scalar()
    avg_score = round(float(avg_score_raw), 1) if avg_score_raw is not None else None

    # Upcoming deadlines (next 7 days, published, not yet submitted final)
    now = datetime.now(timezone.utc)
    upcoming_result = await db.execute(
        select(Assignment, Classroom.name.label("classroom_name"))
        .join(Enrollment, Enrollment.classroom_id == Assignment.classroom_id)
        .join(Classroom, Classroom.id == Assignment.classroom_id)
        .outerjoin(
            Submission,
            (Submission.assignment_id == Assignment.id)
            & (Submission.student_id == student_id)
            & (Submission.is_final == True),  # noqa: E712
        )
        .where(
            Enrollment.user_id == student_id,
            Enrollment.role == EnrollmentRole.student,
            Assignment.is_published == True,  # noqa: E712
            Assignment.deadline > now,
            Submission.id == None,  # noqa: E711  — not yet submitted
        )
        .order_by(Assignment.deadline)
        .limit(5)
    )
    upcoming = [
        {
            "id": str(a.id),
            "title": a.title,
            "classroom_name": cn,
            "deadline": a.deadline.isoformat(),
            "total_marks": a.total_marks,
        }
        for a, cn in upcoming_result.all()
    ]

    # Recent grades
    recent_grades_result = await db.execute(
        select(Grade, Assignment.title, Classroom.name.label("classroom_name"))
        .join(Assignment, Assignment.id == Grade.assignment_id)
        .join(Classroom, Classroom.id == Assignment.classroom_id)
        .where(
            Grade.student_id == student_id,
            Grade.is_released == True,  # noqa: E712
        )
        .order_by(Grade.graded_at.desc())
        .limit(5)
    )
    recent_grades = [
        {
            "id": str(g.id),
            "assignment_title": at,
            "classroom_name": cn,
            "total_score": g.total_score,
            "graded_at": g.graded_at.isoformat(),
        }
        for g, at, cn in recent_grades_result.all()
    ]

    return {
        "role": "student",
        "enrolled_classes": enrolled_classes,
        "active_assignments": active_assignments,
        "total_submissions": total_submissions,
        "avg_score": avg_score,
        "upcoming_deadlines": upcoming,
        "recent_grades": recent_grades,
    }


async def get_teacher_stats(db: AsyncSession, teacher_id: UUID) -> dict:
    """
    Returns a stats snapshot for the teacher dashboard.

    Fields:
      - active_classes      classrooms created by this teacher
      - total_assignments   assignments published
      - pending_grades      final submissions not yet graded
    """
    # Classrooms created
    class_result = await db.execute(
        select(func.count(Classroom.id)).where(Classroom.created_by == teacher_id)
    )
    active_classes = class_result.scalar() or 0

    # Assignments published
    assign_result = await db.execute(
        select(func.count(Assignment.id)).where(
            Assignment.created_by == teacher_id,
            Assignment.is_published == True,  # noqa: E712
        )
    )
    total_assignments = assign_result.scalar() or 0

    # Final submissions that have no Grade row yet (pending grading)
    pending_result = await db.execute(
        select(func.count(Submission.id))
        .outerjoin(Grade, Grade.submission_id == Submission.id)
        .join(Assignment, Assignment.id == Submission.assignment_id)
        .where(
            Assignment.created_by == teacher_id,
            Submission.is_final == True,   # noqa: E712
            Grade.id == None,              # noqa: E711
        )
    )
    pending_grades = pending_result.scalar() or 0

    return {
        "role": "teacher",
        "active_classes": active_classes,
        "total_assignments": total_assignments,
        "pending_grades": pending_grades,
    }


async def get_grade_trends(db: AsyncSession, student_id: UUID) -> list:
    """Returns chronological grade data for the student trend chart."""
    result = await db.execute(
        select(Grade, Assignment.title, Assignment.total_marks)
        .join(Assignment, Assignment.id == Grade.assignment_id)
        .where(
            Grade.student_id == student_id,
            Grade.is_released == True,  # noqa: E712
        )
        .order_by(Grade.graded_at)
        .limit(50)
    )
    return [
        {
            "assignment_title": title,
            "score": g.total_score,
            "total_marks": total,
            "pct": round((g.total_score / total) * 100, 1) if total > 0 else 0,
            "graded_at": g.graded_at.isoformat(),
        }
        for g, title, total in result.all()
    ]


async def get_classroom_analytics(db: AsyncSession, classroom_id: UUID, current_user) -> dict:
    """Grade distribution and submission stats for a classroom (teacher only)."""
    from fastapi import HTTPException
    from app.models.classroom import Enrollment, EnrollmentRole

    # Verify teacher access
    if current_user.role != "admin":
        result = await db.execute(
            select(Enrollment).where(
                Enrollment.classroom_id == classroom_id,
                Enrollment.user_id == current_user.id,
                Enrollment.role == EnrollmentRole.co_teacher,
            )
        )
        if not result.scalars().first():
            raise HTTPException(status_code=403, detail="Teachers only")

    # Get all released grades for this classroom
    grades_result = await db.execute(
        select(Grade.total_score, Assignment.total_marks)
        .join(Assignment, Assignment.id == Grade.assignment_id)
        .where(
            Assignment.classroom_id == classroom_id,
            Grade.is_released == True,  # noqa: E712
        )
    )
    grades_data = grades_result.all()

    buckets = {"0-39": 0, "40-59": 0, "60-74": 0, "75-89": 0, "90-100": 0}
    for score, total in grades_data:
        if total > 0:
            pct = (score / total) * 100
            if pct < 40:
                buckets["0-39"] += 1
            elif pct < 60:
                buckets["40-59"] += 1
            elif pct < 75:
                buckets["60-74"] += 1
            elif pct < 90:
                buckets["75-89"] += 1
            else:
                buckets["90-100"] += 1

    avg = (
        round(sum((s / t) * 100 for s, t in grades_data if t > 0) / len(grades_data), 1)
        if grades_data else 0
    )

    return {
        "grade_distribution": [{"range": k, "count": v} for k, v in buckets.items()],
        "average_percentage": avg,
        "total_grades": len(grades_data),
    }
