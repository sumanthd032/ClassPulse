"""Assignment business logic."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment, RubricCriterion
from app.models.classroom import Enrollment
from app.models.user import User
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError


async def _assert_teacher_of_classroom(db: AsyncSession, teacher: User, classroom_id: uuid.UUID):
    """Raise 403 if the user is not the teacher/co-teacher of the classroom."""
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == teacher.id,
            Enrollment.classroom_id == classroom_id,
            Enrollment.role == "co_teacher",
        )
    )
    if not result.scalar_one_or_none():
        raise ForbiddenError("You are not a teacher of this classroom.")


async def create_assignment(
    db: AsyncSession, teacher: User, classroom_id: uuid.UUID, data: dict
) -> Assignment:
    await _assert_teacher_of_classroom(db, teacher, classroom_id)

    criteria_data = data.pop("rubric_criteria", [])

    assignment = Assignment(
        classroom_id=classroom_id,
        created_by=teacher.id,
        **data,
    )
    db.add(assignment)
    await db.flush()   # need assignment.id for criteria FKs

    for idx, c in enumerate(criteria_data):
        criterion = RubricCriterion(
            assignment_id=assignment.id,
            name=c["name"],
            max_marks=c["max_marks"],
            order_index=c.get("order_index", idx),
            levels=c["levels"],
        )
        db.add(criterion)

    await db.commit()
    await db.refresh(assignment)
    return assignment


async def get_assignment_with_rubric(db: AsyncSession, assignment_id: uuid.UUID) -> Assignment:
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("Assignment")

    criteria_result = await db.execute(
        select(RubricCriterion)
        .where(RubricCriterion.assignment_id == assignment_id)
        .order_by(RubricCriterion.order_index)
    )
    assignment.__dict__["rubric_criteria"] = list(criteria_result.scalars().all())
    return assignment


async def list_assignments(db: AsyncSession, classroom_id: uuid.UUID) -> list[Assignment]:
    result = await db.execute(
        select(Assignment).where(Assignment.classroom_id == classroom_id)
        .order_by(Assignment.deadline)
    )
    return list(result.scalars().all())


async def publish_assignment(db: AsyncSession, assignment_id: uuid.UUID, teacher: User) -> Assignment:
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("Assignment")
    if assignment.created_by != teacher.id:
        raise ForbiddenError("Only the assignment creator can publish it.")
    if assignment.is_published:
        raise BadRequestError("Assignment is already published.")

    assignment.is_published = True
    await db.commit()
    await db.refresh(assignment)
    # Phase 2: publish WebSocket event to classroom channel here
    return assignment


async def update_assignment(
    db: AsyncSession, assignment_id: uuid.UUID, teacher: User, updates: dict
) -> Assignment:
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("Assignment")
    if assignment.created_by != teacher.id:
        raise ForbiddenError("Only the assignment creator can update it.")
    if assignment.is_published:
        raise BadRequestError("Cannot edit a published assignment that has submissions.")

    for field, value in updates.items():
        if value is not None:
            setattr(assignment, field, value)

    await db.commit()
    await db.refresh(assignment)
    return assignment
