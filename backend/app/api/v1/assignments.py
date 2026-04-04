"""Assignment endpoints."""

import uuid
from fastapi import APIRouter

from app.dependencies import DbSession, CurrentUser, TeacherUser
from app.schemas.assignment import (
    CreateAssignmentRequest, UpdateAssignmentRequest, AssignmentResponse
)
from app.services import assignment_service

router = APIRouter()


@router.post("/classrooms/{classroom_id}/assignments", response_model=AssignmentResponse, status_code=201)
async def create_assignment(
    classroom_id: uuid.UUID,
    body: CreateAssignmentRequest,
    db: DbSession,
    current_user: TeacherUser,
):
    """
    Create an assignment with a rubric.
    The rubric_criteria array defines per-criterion mark allocation and level descriptors.
    Assignment starts as unpublished (draft) — students can't see it until /publish is called.
    """
    data = body.model_dump()
    data["rubric_criteria"] = [
        {
            "name": c.name,
            "max_marks": c.max_marks,
            "order_index": c.order_index,
            "levels": c.levels.model_dump(),
        }
        for c in body.rubric_criteria
    ]
    assignment = await assignment_service.create_assignment(db, current_user, classroom_id, data)
    return await assignment_service.get_assignment_with_rubric(db, assignment.id)


@router.get("/classrooms/{classroom_id}/assignments", response_model=list[AssignmentResponse])
async def list_assignments(classroom_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    assignments = await assignment_service.list_assignments(db, classroom_id)
    # Attach rubric to each (TODO: optimise with a join in Phase 4)
    result = []
    for a in assignments:
        result.append(await assignment_service.get_assignment_with_rubric(db, a.id))
    return result


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(assignment_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    return await assignment_service.get_assignment_with_rubric(db, assignment_id)


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: uuid.UUID,
    body: UpdateAssignmentRequest,
    db: DbSession,
    current_user: TeacherUser,
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    return await assignment_service.update_assignment(db, assignment_id, current_user, updates)


@router.post("/{assignment_id}/publish", response_model=AssignmentResponse)
async def publish_assignment(assignment_id: uuid.UUID, db: DbSession, current_user: TeacherUser):
    """
    Publish the assignment — makes it visible to enrolled students.
    Phase 2 will add: WebSocket broadcast to all enrolled students.
    """
    return await assignment_service.publish_assignment(db, assignment_id, current_user)
