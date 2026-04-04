"""Grading business logic."""

import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grade import Grade
from app.models.submission import Submission
from app.models.user import User
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError


async def grade_submission(
    db: AsyncSession, teacher: User, submission_id: uuid.UUID, grades_data: list[dict]
) -> list[Grade]:
    """
    Teacher grades a final submission using rubric click-scoring.
    Each criterion gets: score, level (excellent/good/average/poor), and feedback text.
    """
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise NotFoundError("Submission")
    if not submission.is_final:
        raise BadRequestError("Can only grade final submissions.")

    # Delete existing grades (allows teacher to re-grade)
    from sqlalchemy import delete
    await db.execute(delete(Grade).where(Grade.submission_id == submission_id))

    grades = []
    for g in grades_data:
        grade = Grade(
            submission_id=submission_id,
            criterion_id=g["criterion_id"],
            score=g["score"],
            level=g["level"],
            feedback=g["feedback"],
            graded_by=teacher.id,
            is_released=False,
        )
        db.add(grade)
        grades.append(grade)

    await db.commit()
    for g in grades:
        await db.refresh(g)
    return grades


async def release_grades(db: AsyncSession, teacher: User, assignment_id: uuid.UUID) -> int:
    """
    Release all grades for an assignment — makes them visible to students.
    Returns the count of grades released.
    Phase 2: this also broadcasts a grade_released WebSocket event to each student.
    """
    # Get all final submissions for this assignment
    subs_result = await db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
            Submission.is_final == True,
        )
    )
    sub_ids = [s.id for s in subs_result.scalars().all()]

    if not sub_ids:
        return 0

    result = await db.execute(
        update(Grade)
        .where(Grade.submission_id.in_(sub_ids), Grade.is_released == False)
        .values(is_released=True)
        .returning(Grade.id)
    )
    released = result.fetchall()
    await db.commit()
    return len(released)


async def get_submission_grades(db: AsyncSession, submission_id: uuid.UUID) -> list[Grade]:
    result = await db.execute(select(Grade).where(Grade.submission_id == submission_id))
    return list(result.scalars().all())
