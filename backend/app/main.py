"""
ClassPulse API — Main Application Entry Point

Registers all routers, configures CORS middleware, and exposes a health-check
endpoint.  Swagger UI is available at /api/docs when running locally.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    admin,
    announcements,
    assignments,
    auth,
    classrooms,
    comments,
    dashboard,
    files,
    grading,
    materials,
    notifications,
    submissions,
    topics,
    websocket,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — create upload directory on startup."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="ClassPulse API",
    description=(
        "Backend for the ClassPulse Classroom Management Platform. "
        "Supports three roles: Student, Teacher, and Admin. "
        "Core innovation: LLM-powered rubric-aligned draft feedback loop."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    redirect_slashes=False,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router,          prefix="/api/v1/auth")
app.include_router(classrooms.router,    prefix="/api/v1/classrooms")
app.include_router(assignments.router,   prefix="/api/v1")
app.include_router(announcements.router, prefix="/api/v1")
app.include_router(topics.router,        prefix="/api/v1")
app.include_router(materials.router,     prefix="/api/v1")
app.include_router(comments.router,      prefix="/api/v1")
app.include_router(submissions.router,   prefix="/api/v1")
app.include_router(grading.router,       prefix="/api/v1")
app.include_router(dashboard.router,     prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(files.router,         prefix="/api/v1")
app.include_router(admin.router,         prefix="/api/v1")
app.include_router(websocket.router)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """Returns the running status and API version."""
    return {"status": "ok", "version": app.version}
