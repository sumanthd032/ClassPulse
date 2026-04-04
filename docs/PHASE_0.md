# Phase 0 — Project Setup & Architecture

This document is the canonical reference for the ClassPulse project structure, technology choices, and architectural decisions established in Phase 0. Read this before touching any code.

---

## 1. What is ClassPulse?

ClassPulse is a classroom management platform built for Indian engineering colleges (300+ student batches). Its core innovation is the **Draft → AI Feedback → Improve → Final Submit** loop:

1. Teacher creates an assignment with a rubric (criteria + level descriptors).
2. Student submits a draft at any time before the deadline.
3. System evaluates the draft against the rubric using an LLM and returns per-criterion, actionable feedback in < 30 seconds.
4. Student improves and resubmits (up to N drafts).
5. Student makes a final submission.
6. Teacher grades using rubric click-scoring (AI-suggested grades pre-filled). Releases grades in bulk.

The AI coaches — the teacher decides.

**Three user roles:** Student, Teacher, Admin/HOD.

---

## 2. Technology Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite | Fast DX, type-safe, industry standard |
| Styling | Tailwind CSS | Utility-first, no CSS file sprawl |
| State | Zustand (global) + React Query (server) | Minimal boilerplate, right tool per layer |
| Forms | React Hook Form + Zod | Performant, schema validation |
| Charts | Recharts | React-native charting for analytics views |
| Backend | FastAPI (Python 3.12) | Async-native, auto OpenAPI docs, fast |
| Database | PostgreSQL 16 | Relational integrity, JSONB for flexible fields |
| ORM | SQLAlchemy 2.0 async | Async-native, Alembic migrations |
| Task queue | Celery + Redis | Battle-tested async jobs, beat scheduler |
| Real-time | FastAPI WebSocket + Redis pub/sub | No extra service needed; Redis already present |
| Reverse proxy | Nginx | SSL termination, WS upgrade, rate limiting |
| Containerization | Docker + Docker Compose | Reproducible dev and prod environments |
| Deployment | Render / AWS EC2 | Render for demo (free tier); EC2 for production |
| LLM | OpenAI GPT-4o-mini or Gemini 1.5 Flash | Cost-effective at high volume |

---

## 3. Directory Structure

```
ClassPulse/
├── backend/                        # FastAPI application
│   ├── app/
│   │   ├── main.py                 # FastAPI app, CORS, router mount
│   │   ├── config.py               # Pydantic-settings (reads .env)
│   │   ├── database.py             # Async SQLAlchemy engine + session
│   │   ├── dependencies.py         # get_current_user, require_teacher, require_admin
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py       # Mounts all sub-routers under /api/v1
│   │   │       ├── auth.py         # POST /auth/register|login|refresh, GET /auth/me
│   │   │       ├── classrooms.py   # CRUD + join + analytics
│   │   │       ├── assignments.py  # CRUD + publish + rubric
│   │   │       ├── submissions.py  # submit-draft, submit-final, my-submissions
│   │   │       ├── grading.py      # grade, release-grades, bulk-feedback
│   │   │       └── dashboard.py    # deadlines, grade-trends, grading-queue, at-risk
│   │   ├── core/
│   │   │   ├── security.py         # create_access_token, verify_token, hash_password
│   │   │   └── exceptions.py       # NotFoundError, ForbiddenError, etc.
│   │   ├── models/                 # SQLAlchemy ORM models (one file per table)
│   │   │   ├── user.py
│   │   │   ├── classroom.py
│   │   │   ├── assignment.py
│   │   │   ├── submission.py
│   │   │   ├── grade.py
│   │   │   ├── notification.py
│   │   │   └── ai_feedback.py
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   │   └── (mirrors models/)
│   │   ├── services/               # Business logic, no FastAPI coupling
│   │   │   ├── auth_service.py
│   │   │   ├── classroom_service.py
│   │   │   ├── assignment_service.py
│   │   │   ├── submission_service.py
│   │   │   ├── grading_service.py
│   │   │   ├── notification_service.py
│   │   │   └── llm_service.py      # Prompt building, LLM call, response parsing
│   │   ├── workers/
│   │   │   ├── celery_app.py       # Celery instance + config
│   │   │   ├── beat_schedule.py    # Periodic task definitions
│   │   │   └── tasks/
│   │   │       ├── ai_feedback.py  # generate_ai_feedback (Phase 1)
│   │   │       ├── notifications.py # send_deadline_reminders, cleanup (Phase 2)
│   │   │       ├── similarity.py   # detect_similarity TF-IDF (Phase 3)
│   │   │       ├── analytics.py    # detect_at_risk_students (Phase 3)
│   │   │       └── reports.py      # generate_report_pdf (Phase 3)
│   │   └── websocket/
│   │       ├── manager.py          # WebSocketManager — Redis pub/sub bridge
│   │       └── handlers.py         # /ws/notifications endpoint (Phase 2)
│   ├── migrations/                 # Alembic
│   │   └── versions/
│   ├── tests/
│   ├── Dockerfile                  # API container (uvicorn, 4 workers)
│   ├── Dockerfile.worker           # Worker/beat container (celery)
│   ├── requirements.txt
│   └── alembic.ini
│
├── frontend/                       # React SPA
│   ├── src/
│   │   ├── api/                    # Axios functions per domain
│   │   ├── components/
│   │   │   ├── common/             # Button, Input, Modal, Badge, LoadingSpinner
│   │   │   ├── layout/             # Navbar, Sidebar, PageLayout
│   │   │   ├── classroom/
│   │   │   ├── assignment/         # AssignmentForm, RubricBuilder
│   │   │   ├── submission/         # SubmissionEditor, AIFeedbackPanel, DraftHistory
│   │   │   ├── grading/            # RubricClickGrader, BulkFeedbackModal
│   │   │   └── notifications/
│   │   ├── pages/
│   │   │   ├── auth/               # LoginPage, RegisterPage
│   │   │   ├── student/            # Dashboard, ClassroomPage, AssignmentPage
│   │   │   ├── teacher/            # Dashboard, CreateAssignment, GradingPage
│   │   │   └── admin/              # AdminDashboard
│   │   ├── store/                  # Zustand stores
│   │   ├── hooks/                  # useAuth, useWebSocket, useDeadlineCalendar
│   │   ├── types/index.ts          # All TypeScript interfaces and enums
│   │   └── utils/                  # dateUtils, gradeUtils, constants
│   ├── vite.config.ts              # Dev proxy: /api → :8000, /ws → :8000
│   ├── tailwind.config.js
│   └── Dockerfile                  # Builds React → static files for Nginx
│
├── nginx/
│   ├── nginx.conf                  # Reverse proxy + WS upgrade + rate limiting
│   └── Dockerfile                  # Nginx + React static files
│
├── docs/
│   ├── PHASES.md                   # This project's 5-phase roadmap
│   └── PHASE_0.md                  # This file
│
├── docker-compose.yml              # Production-ready 6-service stack
├── docker-compose.dev.yml          # Dev override (hot reload)
├── .env.example                    # All required env vars documented
└── .gitignore
```

---

## 4. System Architecture

### 4.1 Six-Container Stack

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (React SPA)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────────────┐
│                    nginx (port 80/443)                       │
│  /api/*  → FastAPI :8000    /ws/* → WebSocket :8000          │
│  /*      → React static files                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              api (FastAPI + Uvicorn, 4 workers)              │
│  - REST endpoints (/api/v1/*)                               │
│  - WebSocket handler (/ws/notifications)                    │
│  - Pushes Celery tasks to Redis queue                       │
└────────────┬─────────────────────────────────┬──────────────┘
             │ SQLAlchemy (asyncpg)             │ Redis pub/sub + task queue
┌────────────▼────────┐            ┌────────────▼────────────┐
│  db (PostgreSQL 16) │            │    redis (Redis 7)       │
│  - All relational   │            │  - Celery broker         │
│    data             │            │  - WS pub/sub channels   │
└─────────────────────┘            │  - Rate limit counters   │
                                   │  - LLM response cache    │
                                   └────────────┬────────────┘
                                                │
                              ┌─────────────────┴──────────────┐
                              │                                 │
               ┌──────────────▼────────────┐  ┌───────────────▼───────────┐
               │  worker (Celery worker)    │  │  beat (Celery Beat)       │
               │  - generate_ai_feedback   │  │  - Hourly deadline reminders│
               │  - detect_similarity      │  │  - Daily at-risk detection │
               │  - generate_report_pdf    │  │  - Weekly cleanup          │
               └───────────────────────────┘  └───────────────────────────┘
```

### 4.2 Request Flow (Happy Path)

1. **Browser** sends `POST /api/v1/assignments/:id/submit-draft` with JWT in Authorization header.
2. **Nginx** routes `/api/*` to FastAPI upstream.
3. **FastAPI** verifies JWT → validates draft count → creates `Submission` record → pushes `generate_ai_feedback` task to Redis queue.
4. **Celery worker** picks up task → calls LLM API → stores `AIFeedback` records → publishes `feedback_ready` event to `user:{student_id}:notifications` Redis channel.
5. **FastAPI WebSocket handler** (subscribed to that channel) receives the event → pushes it to the student's WebSocket connection.
6. **Browser** receives WebSocket event → React Query invalidates submission query → AI feedback panel renders.

### 4.3 Database Schema (Core Tables)

```
users ──────────────── classrooms
  │                        │
  │ (enrollments)          │ (assignments)
  │                        │
  └── submissions ─────────┘
        │
        ├── ai_feedback (per draft)
        └── grades (per final submission)

rubric_criteria ──── assignments
notifications ──── users
```

All tables use UUID primary keys. `created_at` / `updated_at` with timezone on every table.

---

## 5. API Design Conventions

- **Prefix:** `/api/v1/`
- **Auth:** JWT Bearer token in `Authorization: Bearer <token>` header.
- **Responses:** All JSON. HTTP status codes are semantic (200, 201, 400, 401, 403, 404, 422, 500).
- **Errors:** `{ "detail": "human readable message" }`
- **Pagination:** Cursor-based for lists > 100 items (not needed in Phase 1, added in Phase 4).

### Endpoint map at a glance

```
Auth:        POST /auth/register|login|refresh    GET /auth/me
Classrooms:  POST|GET /classrooms                 POST /classrooms/join
             GET|PUT /classrooms/:id              GET /classrooms/:id/analytics
Assignments: POST|GET /classrooms/:id/assignments
             GET|PUT /assignments/:id             POST /assignments/:id/publish
             GET /assignments/:id/submissions
Submissions: POST /assignments/:id/submit-draft|submit-final
             GET /assignments/:id/my-submissions  GET /submissions/:id/feedback
Grading:     POST /submissions/:id/grade
             POST /assignments/:id/release-grades|bulk-feedback
Dashboard:   GET /dashboard/deadlines|grade-trends|grading-queue|at-risk
WebSocket:   WS  /ws/notifications
```

---

## 6. Environment Variables

All config flows through environment variables. No hardcoded values anywhere. See `.env.example` for the full list.

| Variable | Used by | Notes |
|---|---|---|
| `DATABASE_URL` | api, worker, beat | `postgresql+asyncpg://...` |
| `REDIS_URL` | api, worker, beat | `redis://redis:6379/0` |
| `JWT_SECRET` | api | Min 32 chars, random |
| `LLM_API_KEY` | worker | OpenAI or Gemini key |
| `LLM_MODEL` | worker | `gpt-4o-mini` or `gemini-1.5-flash` |
| `CORS_ORIGINS` | api | Comma-separated allowed origins |
| `AWS_S3_BUCKET` | worker (Phase 3) | Leave empty in dev |

---

## 7. Development Workflow

### First-time setup

```bash
# 1. Clone and enter project
cd ClassPulse

# 2. Copy env file
cp .env.example .env
# Edit .env — set JWT_SECRET and LLM_API_KEY at minimum

# 3. Start infrastructure (DB + Redis only, for local backend dev)
docker compose up db redis -d

# 4. Backend — local Python
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head          # run migrations
uvicorn app.main:app --reload  # hot reload on :8000

# 5. Frontend — local Node
cd frontend
npm install
npm run dev                   # Vite dev server on :5173, proxies /api to :8000
```

### Full Docker stack

```bash
docker compose up --build    # all 6 containers
# API docs at http://localhost:8000/api/docs (debug mode only)
# App at http://localhost
```

### Running tests

```bash
cd backend
pytest tests/ -v
```

---

## 8. Key Design Decisions

**Why FastAPI over Django?**
Async-native from day one. WebSocket and Celery integration is cleaner. Auto OpenAPI docs. For a greenfield project this size, Django's batteries add friction.

**Why Zustand over Redux?**
ClassPulse's client state is shallow: auth token, notification list, active classroom. Zustand handles this in < 50 lines. Redux is overkill.

**Why not use Django Channels for WebSocket?**
ClassPulse uses FastAPI, not Django. Native FastAPI WebSocket + Redis pub/sub is simpler and avoids a second framework just for WebSocket.

**Why Redis for LLM caching?**
If a student submits identical content twice (copy-paste, double-click), we serve the cached feedback instantly without an LLM API call. Cache key: `SHA256(content + rubric_id)`. TTL: 1 hour.

**Why TF-IDF for similarity detection (not an embedding model)?**
Speed and cost. TF-IDF runs locally in < 1 second on 300 submissions. An embedding model costs money per call and adds latency. For plagiarism flagging (not detection), TF-IDF cosine similarity > 0.85 is sufficient.

**Why not auto-assign grades?**
The PRD is explicit: "AI suggests, teacher decides. No grade is ever auto-assigned without teacher approval." This is a trust and liability decision, not a technical one.

---

## 9. Phase 0 Completion Checklist

- [x] Directory structure created
- [x] `docker-compose.yml` with 6 services
- [x] `docker-compose.dev.yml` dev override
- [x] `.env.example` with all variables documented
- [x] `.gitignore`
- [x] Backend: `main.py`, `config.py`, `database.py`, router tree
- [x] Backend: all module stubs (models, schemas, services, workers, websocket)
- [x] Backend: `Dockerfile` + `Dockerfile.worker`
- [x] Backend: `requirements.txt`, `alembic.ini`
- [x] Frontend: `package.json`, `vite.config.ts`, `tsconfig.json`
- [x] Frontend: Tailwind + PostCSS config
- [x] Frontend: all page, component, store, hook, util stubs
- [x] Frontend: `src/types/index.ts` with all TypeScript types
- [x] Nginx: `nginx.conf` + `Dockerfile`
- [x] Docs: `PHASES.md` (5-phase roadmap)
- [x] Docs: `PHASE_0.md` (this file)

**Next step:** Begin Phase 1 — start with `backend/app/models/` and `backend/migrations/versions/0001_initial.py`.
