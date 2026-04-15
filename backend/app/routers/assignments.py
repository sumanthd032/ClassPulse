"""
Assignment routes.

POST   /classrooms/{classroom_id}/assignments         — create assignment + rubric
GET    /classrooms/{classroom_id}/assignments         — list all assignments in classroom
GET    /assignments/{assignment_id}                   — get assignment detail with rubric
PATCH  /assignments/{assignment_id}                   — update title/deadline/publish flag
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentResponse, AssignmentUpdate
from app.services import assignment_service

router = APIRouter(tags=["Assignments"])


@router.post(
    "/classrooms/{classroom_id}/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an assignment with a rubric (teacher only)",
)
async def create_assignment(
    classroom_id: UUID,
    request: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates the assignment and its rubric criteria in one atomic transaction.
    Business rule: the sum of all `criteria[*].max_marks` must equal `total_marks`.
    Students enrolled in the classroom receive a NEW_ASSIGNMENT notification.
    """
    return await assignment_service.create_assignment(db, classroom_id, request, current_user)


@router.get(
    "/classrooms/{classroom_id}/assignments",
    response_model=List[AssignmentResponse],
    summary="List all assignments in a classroom",
)
async def list_assignments(
    classroom_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all assignments for the classroom (newest first).
    Students only see published assignments; teachers see all.
    """
    return await assignment_service.list_assignments(db, classroom_id, current_user)


@router.get(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse,
    summary="Get assignment detail including rubric",
)
async def get_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns full assignment details including all rubric criteria."""
    return await assignment_service.get_assignment_detail(db, assignment_id, current_user)


@router.patch(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse,
    summary="Update assignment metadata (teacher only)",
)
async def update_assignment(
    assignment_id: UUID,
    request: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially updates an assignment (title, description, deadline, is_published).
    Any teacher enrolled in the classroom can call this.
    """
    return await assignment_service.update_assignment(db, assignment_id, request, current_user)


@router.delete(
    "/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an assignment (teacher only)",
)
async def delete_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletes an assignment and all associated rubric criteria."""
    from sqlalchemy.future import select as sa_select
    from app.models.assignment import Assignment
    from app.models.classroom import Enrollment, EnrollmentRole
    from fastapi import HTTPException

    result = await db.execute(sa_select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalars().first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if current_user.role != "admin":
        enroll_result = await db.execute(
            sa_select(Enrollment).where(
                Enrollment.classroom_id == assignment.classroom_id,
                Enrollment.user_id == current_user.id,
                Enrollment.role == EnrollmentRole.co_teacher,
            )
        )
        if not enroll_result.scalars().first():
            raise HTTPException(status_code=403, detail="Only teachers can delete assignments")

    await db.delete(assignment)
    await db.commit()
