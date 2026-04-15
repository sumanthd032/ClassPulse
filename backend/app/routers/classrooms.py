"""
Classroom routes.

POST   /                          — create a classroom (teacher)
POST   /join                      — join a classroom via code (student)
GET    /                          — list all my classrooms
GET    /{classroom_id}            — get classroom detail
PATCH  /{classroom_id}            — update classroom settings (teacher)
GET    /{classroom_id}/students   — list enrolled students (teacher)
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.classroom import (
    ClassroomCreate,
    ClassroomJoin,
    ClassroomResponse,
    ClassroomUpdate,
    EnrollmentResponse,
    StudentListItem,
)
from app.services import classroom_service

router = APIRouter(tags=["Classrooms"])


@router.post(
    "",
    response_model=ClassroomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new classroom (teacher only)",
)
async def create_classroom(
    request: ClassroomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a classroom and auto-enrolls the creator as co_teacher.
    A unique 6-character join code is generated automatically.
    Students receive a 403.
    """
    return await classroom_service.create_classroom(db, request, current_user)


@router.post("/join", response_model=ClassroomResponse, summary="Join a classroom via join code")
async def join_classroom(
    request: ClassroomJoin,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enrolls the caller as a student in the matching classroom.
    Returns 404 if the code is invalid, 409 if already enrolled.
    """
    return await classroom_service.join_classroom(db, request.join_code, current_user)


@router.get("", response_model=List[EnrollmentResponse], summary="List all my classrooms")
async def list_my_classrooms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns every classroom the caller has joined or created, with role info."""
    return await classroom_service.get_user_classrooms(db, current_user)


@router.get("/{classroom_id}", response_model=ClassroomResponse, summary="Get classroom detail")
async def get_classroom(
    classroom_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns a single classroom's details. The caller must be enrolled."""
    return await classroom_service.get_classroom_or_404(db, classroom_id, current_user)


@router.patch(
    "/{classroom_id}",
    response_model=ClassroomResponse,
    summary="Update classroom name or settings (teacher only)",
)
async def update_classroom(
    classroom_id: UUID,
    request: ClassroomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially updates classroom metadata and/or the settings JSONB.
    Only the classroom creator can call this endpoint.
    """
    return await classroom_service.update_classroom(db, classroom_id, request, current_user)


@router.get(
    "/{classroom_id}/students",
    response_model=List[StudentListItem],
    summary="List enrolled students (teacher only)",
)
async def list_students(
    classroom_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the full roster of enrolled students for teacher use."""
    return await classroom_service.get_enrolled_students(db, classroom_id, current_user)
