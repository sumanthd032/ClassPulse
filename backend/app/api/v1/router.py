from fastapi import APIRouter

from app.api.v1 import auth, classrooms, assignments, submissions, grading, dashboard

api_v1_router = APIRouter()

# Auth: /api/v1/auth/*
api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Classrooms: /api/v1/classrooms/*
api_v1_router.include_router(classrooms.router, prefix="/classrooms", tags=["classrooms"])

# Assignments are accessed in two ways:
#   /api/v1/classrooms/:id/assignments   (nested — create + list per classroom)
#   /api/v1/assignments/:id              (direct — get, update, publish)
# FastAPI allows including the same router twice with different prefixes.
api_v1_router.include_router(assignments.router, prefix="", tags=["assignments"])

# Submissions: /api/v1/assignments/:id/submit-draft etc
api_v1_router.include_router(submissions.router, prefix="", tags=["submissions"])

# Grading: /api/v1/submissions/:id/grade  and  /api/v1/assignments/:id/release-grades
api_v1_router.include_router(grading.router, prefix="", tags=["grading"])

# Dashboard: /api/v1/dashboard/*
api_v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
