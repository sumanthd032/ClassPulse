"""
Admin service — platform-wide analytics for HOD/Admin role.
"""
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.assignment import Assignment
from app.models.classroom import Classroom, Enrollment
from app.models.grade import Grade
from app.models.submission import Submission
from app.models.user import User, UserRole


async def get_platform_stats(db: AsyncSession) -> dict:
    """Aggregate counts across the entire platform."""

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_students = (await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.student)
    )).scalar() or 0
    total_teachers = (await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.teacher)
    )).scalar() or 0
    total_classrooms = (await db.execute(select(func.count(Classroom.id)))).scalar() or 0
    total_assignments = (await db.execute(select(func.count(Assignment.id)))).scalar() or 0
    total_submissions = (await db.execute(select(func.count(Submission.id)))).scalar() or 0
    total_grades = (await db.execute(select(func.count(Grade.id)))).scalar() or 0
    pending_grades = (await db.execute(
        select(func.count(Submission.id))
        .outerjoin(Grade, Grade.submission_id == Submission.id)
        .where(Submission.is_final == True, Grade.id == None)  # noqa: E711,E712
    )).scalar() or 0

    return {
        "total_users": total_users,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classrooms": total_classrooms,
        "total_assignments": total_assignments,
        "total_submissions": total_submissions,
        "total_grades": total_grades,
        "pending_grades": pending_grades,
    }


async def list_users(db: AsyncSession, role: str | None = None, limit: int = 50, offset: int = 0):
    """Return a paginated list of users, optionally filtered by role."""
    q = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    if role:
        q = q.where(User.role == role)
    result = await db.execute(q)
    users = result.scalars().all()

    count_q = select(func.count(User.id))
    if role:
        count_q = count_q.where(User.role == role)
    total = (await db.execute(count_q)).scalar() or 0

    return {"total": total, "items": users}


async def list_all_classrooms(db: AsyncSession, limit: int = 50, offset: int = 0):
    """Return paginated classrooms with enrollment counts."""
    q = (
        select(Classroom, func.count(Enrollment.id).label("student_count"))
        .outerjoin(Enrollment, Enrollment.classroom_id == Classroom.id)
        .group_by(Classroom.id)
        .order_by(Classroom.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(q)).all()
    total = (await db.execute(select(func.count(Classroom.id)))).scalar() or 0

    return {
        "total": total,
        "items": [
            {
                "id": str(c.id),
                "name": c.name,
                "subject_code": c.subject_code,
                "section": c.section,
                "semester": c.semester,
                "student_count": sc,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c, sc in rows
        ],
    }
