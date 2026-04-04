"""Classroom business logic — no FastAPI coupling, pure DB operations.

Service layer pattern: route handlers call services, services talk to the DB.
This keeps routes thin and makes business logic testable in isolation.
"""

import random
import string
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classroom import Classroom, Enrollment, EnrollmentRole
from app.models.user import User
from app.core.exceptions import NotFoundError, ConflictError, ForbiddenError


def _generate_join_code() -> str:
    """Generate a random 6-char uppercase alphanumeric join code (e.g. 'CSE4A7')."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=6))


async def create_classroom(db: AsyncSession, teacher: User, data: dict) -> Classroom:
    """Create a classroom owned by the teacher. Retries join code on collision."""
    for _ in range(5):   # retry loop in case of join_code collision (extremely rare)
        code = _generate_join_code()
        existing = await db.execute(select(Classroom).where(Classroom.join_code == code))
        if not existing.scalar_one_or_none():
            break

    classroom = Classroom(
        name=data["name"],
        subject_code=data["subject_code"],
        section=data["section"],
        semester=data["semester"],
        join_code=code,
        created_by=teacher.id,
        settings=data["settings"],
    )
    db.add(classroom)
    await db.flush()   # flush to get the ID without committing

    # Auto-enroll the creator as co_teacher so they appear in the enrollment list
    enrollment = Enrollment(
        user_id=teacher.id,
        classroom_id=classroom.id,
        role=EnrollmentRole.co_teacher,
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(classroom)
    return classroom


async def get_user_classrooms(db: AsyncSession, user: User) -> list[Classroom]:
    """Return all classrooms the user is enrolled in or has created."""
    result = await db.execute(
        select(Classroom)
        .join(Enrollment, Enrollment.classroom_id == Classroom.id)
        .where(Enrollment.user_id == user.id)
    )
    return list(result.scalars().all())


async def get_classroom_or_404(db: AsyncSession, classroom_id: uuid.UUID) -> Classroom:
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    if not classroom:
        raise NotFoundError("Classroom")
    return classroom


async def join_classroom(db: AsyncSession, user: User, join_code: str) -> Enrollment:
    """Enroll a student in a classroom using the 6-char code."""
    result = await db.execute(select(Classroom).where(Classroom.join_code == join_code.upper()))
    classroom = result.scalar_one_or_none()
    if not classroom:
        raise NotFoundError("Classroom with that join code")

    # Check already enrolled
    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.classroom_id == classroom.id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("You are already enrolled in this classroom.")

    enrollment = Enrollment(
        user_id=user.id,
        classroom_id=classroom.id,
        role=EnrollmentRole.student,
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


async def update_settings(
    db: AsyncSession, classroom: Classroom, teacher: User, settings: dict
) -> Classroom:
    if classroom.created_by != teacher.id:
        raise ForbiddenError("Only the classroom owner can update settings.")
    classroom.settings = settings
    await db.commit()
    await db.refresh(classroom)
    return classroom
