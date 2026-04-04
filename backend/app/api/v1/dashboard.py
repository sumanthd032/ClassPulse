"""Dashboard endpoints — aggregated views for students and teachers."""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.dependencies import DbSession, CurrentUser, TeacherUser
from app.models.assignment import Assignment
from app.models.classroom import Enrollment
from app.models.submission import Submission
from app.models.grade import Grade

router = APIRouter()


class DeadlineItem(BaseModel):
    assignment_id: str
    assignment_title: str
    classroom_name: str
    deadline: datetime
    has_final_submission: bool
    urgency: str   # "red" | "orange" | "green"


class GradingQueueItem(BaseModel):
    assignment_id: str
    assignment_title: str
    classroom_name: str
    deadline: datetime
    total_submissions: int
    graded_count: int


@router.get("/deadlines", response_model=list[DeadlineItem])
async def get_deadlines(db: DbSession, current_user: CurrentUser):
    """
    Student: all upcoming deadlines across all enrolled classrooms.
    Color-coded by urgency:
      red    = <24h remaining
      orange = <3 days remaining
      green  = >3 days remaining
    """
    # Get all classrooms the student is enrolled in
    enroll_result = await db.execute(
        select(Enrollment).where(Enrollment.user_id == current_user.id)
    )
    classroom_ids = [e.classroom_id for e in enroll_result.scalars().all()]
    if not classroom_ids:
        return []

    # Get published assignments for those classrooms
    from app.models.classroom import Classroom
    assignments_result = await db.execute(
        select(Assignment, Classroom)
        .join(Classroom, Assignment.classroom_id == Classroom.id)
        .where(
            Assignment.classroom_id.in_(classroom_ids),
            Assignment.is_published == True,
        )
        .order_by(Assignment.deadline)
    )
    rows = assignments_result.all()

    now = datetime.now(timezone.utc)
    items = []
    for assignment, classroom in rows:
        deadline = assignment.deadline.replace(tzinfo=timezone.utc)
        diff = deadline - now
        hours = diff.total_seconds() / 3600

        # Check if student already submitted final
        final_sub = await db.execute(
            select(Submission).where(
                Submission.assignment_id == assignment.id,
                Submission.student_id == current_user.id,
                Submission.is_final == True,
            )
        )
        has_final = final_sub.scalar_one_or_none() is not None

        if hours < 0:
            urgency = "red"     # past due
        elif hours < 24:
            urgency = "red"
        elif hours < 72:
            urgency = "orange"
        else:
            urgency = "green"

        items.append(DeadlineItem(
            assignment_id=str(assignment.id),
            assignment_title=assignment.title,
            classroom_name=classroom.name,
            deadline=deadline,
            has_final_submission=has_final,
            urgency=urgency,
        ))

    return items


@router.get("/grading-queue", response_model=list[GradingQueueItem])
async def get_grading_queue(db: DbSession, current_user: TeacherUser):
    """
    Teacher: all assignments that need grading, sorted by deadline proximity.
    Shows total submissions and how many have been graded.
    """
    from app.models.classroom import Classroom
    enroll_result = await db.execute(
        select(Enrollment).where(Enrollment.user_id == current_user.id)
    )
    classroom_ids = [e.classroom_id for e in enroll_result.scalars().all()]
    if not classroom_ids:
        return []

    assignments_result = await db.execute(
        select(Assignment, Classroom)
        .join(Classroom, Assignment.classroom_id == Classroom.id)
        .where(
            Assignment.classroom_id.in_(classroom_ids),
            Assignment.is_published == True,
        )
        .order_by(Assignment.deadline)
    )

    items = []
    for assignment, classroom in assignments_result.all():
        # Count final submissions
        sub_result = await db.execute(
            select(Submission).where(
                Submission.assignment_id == assignment.id,
                Submission.is_final == True,
            )
        )
        submissions = sub_result.scalars().all()
        total = len(submissions)

        # Count how many have at least one grade
        graded = 0
        for sub in submissions:
            grade_check = await db.execute(select(Grade).where(Grade.submission_id == sub.id))
            if grade_check.first():
                graded += 1

        items.append(GradingQueueItem(
            assignment_id=str(assignment.id),
            assignment_title=assignment.title,
            classroom_name=classroom.name,
            deadline=assignment.deadline.replace(tzinfo=timezone.utc),
            total_submissions=total,
            graded_count=graded,
        ))

    return items
