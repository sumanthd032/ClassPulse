"""
Submission service — draft and final submission logic, and feedback retrieval.
"""
from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.assignment import Assignment
from app.models.classroom import Enrollment, EnrollmentRole
from app.models.feedback import AIFeedback
from app.models.submission import Submission
from app.models.user import User, UserRole
from app.schemas.submission import SubmissionCreate


async def _get_assignment_or_404(db: AsyncSession, assignment_id: UUID) -> Assignment:
    """Fetches an assignment by ID or raises 404."""
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalars().first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return assignment


async def submit_draft(
    db: AsyncSession,
    assignment_id: UUID,
    data: SubmissionCreate,
    current_user: User,
) -> Submission:
    """
    Creates a draft submission for a student.

    Business rules:
      - Only students can submit.
      - The student cannot exceed the assignment's `max_drafts` limit.
      - Late submissions are flagged automatically.

    After saving, queues a Celery task (`generate_ai_feedback`) so the student
    receives rubric-aligned LLM feedback asynchronously.
    """
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit assignments",
        )

    assignment = await _get_assignment_or_404(db, assignment_id)

    # Count existing drafts for this student on this assignment
    count_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.assignment_id == assignment_id,
            Submission.student_id == current_user.id,
            Submission.is_final == False,  # noqa: E712
        )
    )
    draft_count = count_result.scalar() or 0

    if draft_count >= assignment.max_drafts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum draft limit ({assignment.max_drafts}) reached for this assignment",
        )

    from datetime import datetime, timezone
    is_late = datetime.now(timezone.utc) > assignment.deadline

    submission = Submission(
        assignment_id=assignment.id,
        student_id=current_user.id,
        content=data.content,
        file_url=data.file_url,
        is_final=False,
        draft_number=draft_count + 1,
        is_late=is_late,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # Queue AI feedback asynchronously — does not block the HTTP response
    from app.workers.ai_feedback import generate_ai_feedback
    generate_ai_feedback.delay(str(submission.id))

    return submission


async def submit_final(
    db: AsyncSession,
    assignment_id: UUID,
    data: SubmissionCreate,
    current_user: User,
) -> Submission:
    """
    Creates the one and only final submission.

    Business rules:
      - Only students can submit.
      - A student can only have one final submission per assignment (enforced by
        a partial unique index in the DB and a check here for a clean error).
      - Late submissions are flagged automatically.

    After saving, queues a Celery plagiarism-check task.
    """
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit assignments",
        )

    assignment = await _get_assignment_or_404(db, assignment_id)

    # Check for existing final submission
    existing_result = await db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
            Submission.student_id == current_user.id,
            Submission.is_final == True,  # noqa: E712
        )
    )
    if existing_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted your final answer for this assignment",
        )

    from datetime import datetime, timezone
    is_late = datetime.now(timezone.utc) > assignment.deadline

    # draft_number=0 is our sentinel for "this is the final, not a numbered draft"
    submission = Submission(
        assignment_id=assignment.id,
        student_id=current_user.id,
        content=data.content,
        file_url=data.file_url,
        is_final=True,
        draft_number=0,
        is_late=is_late,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # Queue plagiarism check + AI auto-grading asynchronously
    from app.workers.similarity import check_plagiarism
    from app.workers.auto_grade import auto_grade_submission
    check_plagiarism.delay(str(submission.id))
    auto_grade_submission.delay(str(submission.id))

    return submission


async def list_submissions_for_assignment(
    db: AsyncSession, assignment_id: UUID, current_user: User
) -> List[Submission]:
    """
    Returns all submissions (drafts + finals) for an assignment.
    Only the teacher of that classroom can call this.
    """
    assignment = await _get_assignment_or_404(db, assignment_id)

    # Verify caller is a teacher in this classroom
    enroll_result = await db.execute(
        select(Enrollment).where(
            Enrollment.classroom_id == assignment.classroom_id,
            Enrollment.user_id == current_user.id,
            Enrollment.role == EnrollmentRole.co_teacher,
        )
    )
    if not enroll_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the classroom teacher can view all submissions",
        )

    result = await db.execute(
        select(Submission)
        .where(Submission.assignment_id == assignment_id)
        .order_by(Submission.submitted_at.desc())
    )
    return result.scalars().all()


async def get_my_submissions(
    db: AsyncSession, assignment_id: UUID, current_user: User
) -> List[Submission]:
    """Returns all drafts and the final submission for the authenticated student."""
    await _get_assignment_or_404(db, assignment_id)

    result = await db.execute(
        select(Submission)
        .where(
            Submission.assignment_id == assignment_id,
            Submission.student_id == current_user.id,
        )
        .order_by(Submission.draft_number)
    )
    return result.scalars().all()


async def get_submission(
    db: AsyncSession, submission_id: UUID, current_user: User
) -> Submission:
    """
    Returns a single submission.
    Students can only fetch their own submissions.
    Teachers can fetch any submission in their classroom.
    """
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalars().first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Students can only see their own work
    if current_user.role == UserRole.student:
        if str(submission.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own submissions",
            )
    else:
        # Teachers must be enrolled in the same classroom
        assignment = await _get_assignment_or_404(db, submission.assignment_id)
        enroll_result = await db.execute(
            select(Enrollment).where(
                Enrollment.classroom_id == assignment.classroom_id,
                Enrollment.user_id == current_user.id,
                Enrollment.role == EnrollmentRole.co_teacher,
            )
        )
        if not enroll_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this submission",
            )

    return submission


async def get_feedback(
    db: AsyncSession, submission_id: UUID, current_user: User
) -> List[AIFeedback]:
    """
    Returns the AI feedback records for a submission.

    Students can only view feedback on their own submissions.
    Teachers (co_teacher) can view feedback for any submission in their classroom.
    Returns an empty list if the Celery worker hasn't completed yet.
    """
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalars().first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if current_user.role == UserRole.student:
        # Students can only see their own feedback
        if str(submission.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view feedback on your own submissions",
            )
    else:
        # Teachers must be co_teacher in the submission's classroom
        assignment = await _get_assignment_or_404(db, submission.assignment_id)
        enroll_result = await db.execute(
            select(Enrollment).where(
                Enrollment.classroom_id == assignment.classroom_id,
                Enrollment.user_id == current_user.id,
                Enrollment.role == EnrollmentRole.co_teacher,
            )
        )
        if not enroll_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this submission's feedback",
            )

    from app.models.assignment import RubricCriteria
    feedback_result = await db.execute(
        select(AIFeedback, RubricCriteria.name, RubricCriteria.max_marks)
        .outerjoin(RubricCriteria, RubricCriteria.id == AIFeedback.criterion_id)
        .where(AIFeedback.submission_id == submission_id)
        .order_by(AIFeedback.generated_at)
    )
    rows = feedback_result.all()
    enriched = []
    for fb, crit_name, crit_max in rows:
        item = {
            "id": fb.id,
            "submission_id": fb.submission_id,
            "criterion_id": fb.criterion_id,
            "criterion_name": crit_name,
            "criterion_max_marks": crit_max,
            "estimated_score": fb.estimated_score,
            "feedback_text": fb.feedback_text,
            "suggested_level": fb.suggested_level,
            "generated_at": fb.generated_at,
        }
        enriched.append(item)
    return enriched
