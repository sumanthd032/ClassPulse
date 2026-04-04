"""Submission business logic — draft submit, final submit, fetch history."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.ai_feedback import AIFeedback
from app.models.user import User
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError


async def submit_draft(
    db: AsyncSession, student: User, assignment_id: uuid.UUID, content: str, file_url: str | None
) -> Submission:
    """
    Submit a draft. Key validations:
    1. Assignment must exist and be published.
    2. Student must not have already made a final submission.
    3. Draft count must not exceed max_drafts.
    4. Deadline enforcement based on late_policy.
    Returns the created Submission. The Celery task is queued by the API endpoint.
    """
    # 1. Fetch assignment
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("Assignment")
    if not assignment.is_published:
        raise BadRequestError("This assignment is not yet published.")

    # 2. Check for existing final submission
    final_check = await db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
            Submission.student_id == student.id,
            Submission.is_final == True,
        )
    )
    if final_check.scalar_one_or_none():
        raise BadRequestError("You have already made a final submission for this assignment.")

    # 3. Count existing drafts
    draft_count_result = await db.execute(
        select(func.count()).where(
            Submission.assignment_id == assignment_id,
            Submission.student_id == student.id,
            Submission.is_final == False,
        )
    )
    draft_count = draft_count_result.scalar_one()
    if draft_count >= assignment.max_drafts:
        raise BadRequestError(
            f"Draft limit reached ({assignment.max_drafts}). Please submit your final version."
        )

    # 4. Check late status
    now = datetime.now(timezone.utc)
    is_late = now > assignment.deadline.replace(tzinfo=timezone.utc)
    if is_late and assignment.late_policy == "block":
        raise BadRequestError("The deadline has passed and late submissions are not allowed.")

    submission = Submission(
        assignment_id=assignment_id,
        student_id=student.id,
        content=content,
        file_url=file_url,
        is_final=False,
        draft_number=draft_count + 1,
        is_late=is_late,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


async def submit_final(
    db: AsyncSession, student: User, assignment_id: uuid.UUID, content: str, file_url: str | None
) -> Submission:
    """Lock in the final submission. Immutable after this point."""
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("Assignment")
    if not assignment.is_published:
        raise BadRequestError("This assignment is not yet published.")

    # Check deadline / late policy
    now = datetime.now(timezone.utc)
    is_late = now > assignment.deadline.replace(tzinfo=timezone.utc)
    if is_late and assignment.late_policy == "block":
        raise BadRequestError("The deadline has passed and late submissions are not allowed.")

    # Check not already finalized
    existing_final = await db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
            Submission.student_id == student.id,
            Submission.is_final == True,
        )
    )
    if existing_final.scalar_one_or_none():
        raise BadRequestError("Final submission already exists.")

    # Count drafts to set draft_number
    draft_count_result = await db.execute(
        select(func.count()).where(
            Submission.assignment_id == assignment_id,
            Submission.student_id == student.id,
        )
    )
    draft_count = draft_count_result.scalar_one()

    submission = Submission(
        assignment_id=assignment_id,
        student_id=student.id,
        content=content,
        file_url=file_url,
        is_final=True,
        draft_number=draft_count + 1,
        is_late=is_late,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


async def get_my_submissions(
    db: AsyncSession, student_id: uuid.UUID, assignment_id: uuid.UUID
) -> list[Submission]:
    """Return all drafts + final submission for a student, with AI feedback attached."""
    subs_result = await db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
            Submission.student_id == student_id,
        ).order_by(Submission.draft_number)
    )
    submissions = list(subs_result.scalars().all())

    for sub in submissions:
        fb_result = await db.execute(
            select(AIFeedback).where(AIFeedback.submission_id == sub.id)
        )
        sub.__dict__["ai_feedback"] = list(fb_result.scalars().all())

    return submissions


async def get_all_submissions_for_assignment(
    db: AsyncSession, assignment_id: uuid.UUID
) -> list[Submission]:
    """Return all final submissions for an assignment (teacher view)."""
    result = await db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
            Submission.is_final == True,
        )
    )
    return list(result.scalars().all())
