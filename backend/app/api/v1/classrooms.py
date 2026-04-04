"""Classroom endpoints."""

import uuid
from fastapi import APIRouter

from app.dependencies import DbSession, CurrentUser, TeacherUser
from app.schemas.classroom import (
    CreateClassroomRequest, JoinClassroomRequest, UpdateClassroomSettingsRequest,
    ClassroomResponse, EnrollmentResponse
)
from app.services import classroom_service

router = APIRouter()


@router.post("", response_model=ClassroomResponse, status_code=201)
async def create_classroom(body: CreateClassroomRequest, db: DbSession, current_user: TeacherUser):
    """
    Create a new classroom. Teacher/admin only.
    Returns the classroom with auto-generated join code.
    """
    classroom = await classroom_service.create_classroom(
        db, current_user,
        data={
            "name": body.name,
            "subject_code": body.subject_code,
            "section": body.section,
            "semester": body.semester,
            "settings": body.settings.model_dump(),
        }
    )
    return classroom


@router.get("", response_model=list[ClassroomResponse])
async def list_classrooms(db: DbSession, current_user: CurrentUser):
    """List all classrooms the current user is enrolled in or created."""
    return await classroom_service.get_user_classrooms(db, current_user)


@router.get("/{classroom_id}", response_model=ClassroomResponse)
async def get_classroom(classroom_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    return await classroom_service.get_classroom_or_404(db, classroom_id)


@router.post("/join", response_model=EnrollmentResponse, status_code=201)
async def join_classroom(body: JoinClassroomRequest, db: DbSession, current_user: CurrentUser):
    """Join a classroom using the 6-char code. Any authenticated user can join."""
    return await classroom_service.join_classroom(db, current_user, body.join_code)


@router.put("/{classroom_id}/settings", response_model=ClassroomResponse)
async def update_settings(
    classroom_id: uuid.UUID,
    body: UpdateClassroomSettingsRequest,
    db: DbSession,
    current_user: TeacherUser,
):
    classroom = await classroom_service.get_classroom_or_404(db, classroom_id)
    return await classroom_service.update_settings(db, classroom, current_user, body.settings.model_dump())
