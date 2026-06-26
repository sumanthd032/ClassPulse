"""
Grading service — grade submission CRUD and grading queue.
"""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from sqlalchemy import delete as sa_delete, or_

from app.models.assignment import Assignment
from app.models.classroom import Enrollment, EnrollmentRole
from app.models.criterion_grade import CriterionGrade
from app.models.grade import Grade
from app.models.submission import Submission
from app.models.user import User, UserRole
from app.schemas.grade import GradeCreate
from app.utils.websocket_manager import manager


async def _get_grade_with_criteria(db: AsyncSession, grade_id: UUID) -> Grade:
    """Load a grade with criterion_grades eagerly to avoid async lazy-load errors."""
    result = await db.execute(
        select(Grade)
        .options(selectinload(Grade.criterion_grades))
        .where(Grade.id == grade_id)
    )
    grade = result.scalars().first()
    if not grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grade not found")
    return grade


async def _verify_teacher_access(
    db: AsyncSession, classroom_id: UUID, user_id: UUID
) -> None:
    """Raises 403 if the caller is not a co_teacher in the classroom."""
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
            detail="Only teachers of this classroom can grade submissions",
        )


async def get_grading_queue(
    db: AsyncSession, assignment_id: UUID, current_user: User
) -> list:
    """
    Returns all final submissions that have NOT been graded yet, enriched with
    student name and email so the teacher can identify submissions without extra calls.
    Only the classroom teacher can access this.
    """
    assign_result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = assign_result.scalars().first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    await _verify_teacher_access(db, assignment.classroom_id, current_user.id)

    # Join submissions with users to get student names inline.
    # Include AI-auto-graded submissions (sentinel: grader_id == student_id) so
    # teachers can review and confirm AI suggestions.
    result = await db.execute(
        select(Submission, User.full_name, User.email)
        .join(User, User.id == Submission.student_id)
        .outerjoin(Grade, Grade.submission_id == Submission.id)
        .where(
            Submission.assignment_id == assignment_id,
            Submission.is_final == True,   # noqa: E712
            or_(
                Grade.id == None,                          # no grade at all  # noqa: E711
                Grade.grader_id == Submission.student_id,  # AI-suggested sentinel
            ),
        )
        .order_by(Submission.submitted_at)
    )
    rows = result.all()

    # Build enriched dicts for the response schema
    items = []
    for submission, student_name, student_email in rows:
        items.append({
            "id": submission.id,
            "student_id": submission.student_id,
            "student_name": student_name,
            "student_email": student_email,
            "content": submission.content,
            "is_final": submission.is_final,
            "draft_number": submission.draft_number,
            "is_late": submission.is_late,
            "similarity_score": submission.similarity_score,
            "similarity_flagged": submission.similarity_flagged,
            "submitted_at": submission.submitted_at,
        })
    return items


async def grade_submission(
    db: AsyncSession,
    submission_id: UUID,
    data: GradeCreate,
    current_user: User,
) -> Grade:
    """
    Creates or updates the grade for a final submission (upsert).

    Rules:
      - Cannot grade drafts (400).
      - Caller must be a co_teacher in the classroom (403).
      - If `is_released=True`, a GRADE_RELEASED WebSocket event is pushed to the student.
    """
    # 1. Fetch submission
    sub_result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = sub_result.scalars().first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if not submission.is_final:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only final submissions can be graded, not drafts",
        )

    # 2. Fetch assignment for classroom_id
    assign_result = await db.execute(
        select(Assignment).where(Assignment.id == submission.assignment_id)
    )
    assignment = assign_result.scalars().first()

    await _verify_teacher_access(db, assignment.classroom_id, current_user.id)

    # 3. Upsert the grade
    grade_result = await db.execute(
        select(Grade).where(Grade.submission_id == submission.id)
    )
    existing = grade_result.scalars().first()

    if existing:
        existing.total_score = data.total_score
        existing.teacher_comments = data.teacher_comments
        existing.is_released = data.is_released
        existing.grader_id = current_user.id
        grade = existing
    else:
        grade = Grade(
            submission_id=submission.id,
            assignment_id=assignment.id,
            student_id=submission.student_id,
            grader_id=current_user.id,
            total_score=data.total_score,
            teacher_comments=data.teacher_comments,
            is_released=data.is_released,
        )
        db.add(grade)

    await db.commit()
    await db.refresh(grade)

    # 3b. Save per-criterion grades if provided
    if data.criterion_scores:
        await db.execute(
            sa_delete(CriterionGrade).where(CriterionGrade.grade_id == grade.id)
        )
        for cs in data.criterion_scores:
            cg = CriterionGrade(
                grade_id=grade.id,
                criterion_id=cs.criterion_id,
                score=cs.score,
                comment=cs.comment,
            )
            db.add(cg)
        await db.commit()
        await db.refresh(grade)

    # 4. Real-time notification if the teacher is releasing the grade right now
    if grade.is_released:
        await manager.send_personal_message(
            {
                "type": "GRADE_RELEASED",
                "title": "Your grade is available!",
                "message": (
                    f"Your teacher released a score of {grade.total_score} "
                    f"for {assignment.title}"
                ),
                "assignment_id": str(assignment.id),
            },
            str(submission.student_id),
        )

    return await _get_grade_with_criteria(db, grade.id)


async def release_all_grades(
    db: AsyncSession, assignment_id: UUID, current_user: User
) -> dict:
    """Release all graded (unreleased) submissions for an assignment at once."""
    assign_result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = assign_result.scalars().first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    await _verify_teacher_access(db, assignment.classroom_id, current_user.id)

    grade_result = await db.execute(
        select(Grade).where(
            Grade.assignment_id == assignment_id,
            Grade.is_released == False,  # noqa: E712
        )
    )
    grades = grade_result.scalars().all()
    count = 0
    for grade in grades:
        grade.is_released = True
        count += 1
        await manager.send_personal_message(
            {
                "type": "GRADE_RELEASED",
                "title": "Your grade is available!",
                "message": f"Your teacher released your grade for {assignment.title}",
                "assignment_id": str(assignment.id),
            },
            str(grade.student_id),
        )
    await db.commit()
    return {"released": count}


async def get_grade(
    db: AsyncSession, submission_id: UUID, current_user: User
) -> Grade:
    """
    Returns the grade for a submission.
    - Teachers always see it.
    - Students only see it when `is_released=True`.
    Raises 404 if the submission or grade doesn't exist.
    """
    sub_result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = sub_result.scalars().first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    grade_result = await db.execute(
        select(Grade)
        .options(selectinload(Grade.criterion_grades))
        .where(Grade.submission_id == submission_id)
    )
    grade = grade_result.scalars().first()

    if not grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grade not yet assigned")

    # Students can only view released grades
    if current_user.role == UserRole.student:
        if str(submission.student_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own grades",
            )
        if not grade.is_released:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your grade has not been released yet",
            )

    return grade
