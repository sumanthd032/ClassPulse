"""
Assignment service — CRUD and rubric management.
"""
from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment, RubricCriteria
from app.models.classroom import Enrollment, EnrollmentRole
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate
from app.utils.notification_helper import create_and_send_notification_async


async def _verify_teacher_access(
    db: AsyncSession, classroom_id: UUID, user_id: UUID
) -> None:
    """
    Raises HTTP 403 if the caller is not enrolled as co_teacher in the classroom.
    This covers both the creator and any co-teachers added later.
    """
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.classroom_id == classroom_id,
            Enrollment.user_id == user_id,
            Enrollment.role == EnrollmentRole.co_teacher,
        )
    )
    if not result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers of this classroom can perform this action",
        )


async def _verify_enrollment(
    db: AsyncSession, classroom_id: UUID, user_id: UUID
) -> None:
    """Raises HTTP 403 if the caller is not enrolled in the classroom at all."""
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.classroom_id == classroom_id,
            Enrollment.user_id == user_id,
        )
    )
    if not result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this classroom",
        )


async def create_assignment(
    db: AsyncSession,
    classroom_id: UUID,
    data: AssignmentCreate,
    current_user: User,
) -> Assignment:
    """
    Creates an assignment + all rubric criteria in a single transaction.

    Business rules:
      - Caller must be a co_teacher in the classroom.
      - The sum of all `criteria[*].max_marks` must equal `total_marks`.

    After creation, all enrolled students receive a NEW_ASSIGNMENT notification.
    """
    await _verify_teacher_access(db, classroom_id, current_user.id)

    # Validate rubric marks add up to the stated total
    criteria_total = sum(c.max_marks for c in data.criteria)
    if criteria_total != data.total_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Rubric criteria max_marks sum ({criteria_total}) does not match "
                f"assignment total_marks ({data.total_marks})"
            ),
        )

    # Create the Assignment
    assignment = Assignment(
        classroom_id=classroom_id,
        title=data.title,
        description=data.description,
        deadline=data.deadline,
        total_marks=data.total_marks,
        submission_type=data.submission_type,
        max_drafts=data.max_drafts,
        late_policy=data.late_policy,
        penalty_per_day=data.penalty_per_day,
        is_published=data.is_published,
        created_by=current_user.id,
    )
    db.add(assignment)
    await db.flush()  # Get assignment.id before creating criteria

    # Create rubric criteria preserving frontend display order
    for idx, c in enumerate(data.criteria):
        db.add(
            RubricCriteria(
                assignment_id=assignment.id,
                name=c.name,
                max_marks=c.max_marks,
                order_index=idx,
                levels=c.levels,
            )
        )

    await db.commit()

    # Reload with criteria for the response
    result = await db.execute(
        select(Assignment)
        .options(selectinload(Assignment.criteria))
        .where(Assignment.id == assignment.id)
    )
    assignment = result.scalars().first()

    # Notify enrolled students only when the assignment is published.
    if assignment.is_published:
        students_result = await db.execute(
            select(Enrollment).where(
                Enrollment.classroom_id == classroom_id,
                Enrollment.role == EnrollmentRole.student,
            )
        )
        for enrollment in students_result.scalars().all():
            await create_and_send_notification_async(
                db=db,
                user_id=str(enrollment.user_id),
                alert_type="NEW_ASSIGNMENT",
                title="New Assignment Posted!",
                message=f"Your teacher posted: {assignment.title}",
            )

    return assignment


async def list_assignments(
    db: AsyncSession, classroom_id: UUID, current_user: User
) -> List[Assignment]:
    """
    Returns all assignments for a classroom.
    - Teachers see ALL assignments (including unpublished drafts).
    - Students only see published assignments.
    """
    await _verify_enrollment(db, classroom_id, current_user.id)

    query = (
        select(Assignment)
        .options(selectinload(Assignment.criteria))
        .where(Assignment.classroom_id == classroom_id)
        .order_by(Assignment.created_at.desc())
    )

    # Filter out unpublished assignments for students
    enroll_result = await db.execute(
        select(Enrollment).where(
            Enrollment.classroom_id == classroom_id,
            Enrollment.user_id == current_user.id,
            Enrollment.role == EnrollmentRole.student,
        )
    )
    if enroll_result.scalars().first():
        query = query.where(Assignment.is_published == True)  # noqa: E712

    result = await db.execute(query)
    return result.scalars().all()


async def get_assignment_detail(
    db: AsyncSession, assignment_id: UUID, current_user: User
) -> Assignment:
    """
    Returns full assignment detail including rubric.
    Verifies the caller is enrolled in the classroom.
    """
    result = await db.execute(
        select(Assignment)
        .options(selectinload(Assignment.criteria))
        .where(Assignment.id == assignment_id)
    )
    assignment = result.scalars().first()

    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    await _verify_enrollment(db, assignment.classroom_id, current_user.id)
    return assignment


async def update_assignment(
    db: AsyncSession,
    assignment_id: UUID,
    data: AssignmentUpdate,
    current_user: User,
) -> Assignment:
    """
    Partially updates an assignment (title, description, deadline, is_published).
    Any classroom teacher can update assignment metadata.
    """
    result = await db.execute(
        select(Assignment)
        .options(selectinload(Assignment.criteria))
        .where(Assignment.id == assignment_id)
    )
    assignment = result.scalars().first()

    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    await _verify_teacher_access(db, assignment.classroom_id, current_user.id)

    if data.title is not None:
        assignment.title = data.title
    if data.description is not None:
        assignment.description = data.description
    if data.deadline is not None:
        assignment.deadline = data.deadline
    if data.is_published is not None:
        assignment.is_published = data.is_published

    await db.commit()
    await db.refresh(assignment)
    return assignment
