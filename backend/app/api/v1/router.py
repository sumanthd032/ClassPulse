from fastapi import APIRouter

from app.api.v1 import auth, classrooms, assignments, submissions, grading, dashboard

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(classrooms.router, prefix="/classrooms", tags=["classrooms"])
api_v1_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_v1_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
api_v1_router.include_router(grading.router, prefix="/grading", tags=["grading"])
api_v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# Assignments are nested under classrooms AND directly accessible by ID.
# FastAPI allows including the same router twice with different prefixes.
from app.api.v1 import assignments as assignments_module
api_v1_router.include_router(
    assignments_module.router, prefix="", tags=["assignments"]
)
