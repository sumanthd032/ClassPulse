# ClassPulse — Phase Completion Tracker

Last updated: 2026-04-13

---

## Phase 0 — Project Scaffold ✅

| Task | Status |
|---|---|
| Directory structure (`backend/`, `frontend/`, `docs/`) | ✅ Done |
| Docker Compose (dev + prod) | ✅ Done |
| Alembic configured + initial migrations | ✅ Done |
| `.env.example` (root + backend) | ✅ Done |
| CI workflow (GitHub Actions) | ✅ Done |

---

## Phase 1 — Core MVP ✅

| Task | Status |
|---|---|
| Auth: register, login, logout, refresh, /me, PATCH /me | ✅ Done |
| Classrooms: CRUD, join, student roster, settings update | ✅ Done |
| Assignments: create + rubric, list, get, update, publish toggle | ✅ Done |
| Submissions: draft (→AI feedback), final (→plagiarism check), list | ✅ Done |
| AI Feedback: LLM-powered per-criterion feedback via Celery | ✅ Done |
| Grading: grade upsert, grading queue, GET grade (role-aware) | ✅ Done |
| Notifications: list, mark read, mark all read | ✅ Done |
| Dashboard: role-aware stats | ✅ Done |
| WebSocket: JWT-authenticated real-time push | ✅ Done |

---

## Phase 2 — Real-Time & Workers ✅

| Task | Status |
|---|---|
| Celery worker: AI feedback with Redis rate limiting | ✅ Done |
| Celery worker: TF-IDF plagiarism/similarity detection | ✅ Done |
| Celery Beat: late penalty cron (midnight UTC) | ✅ Done |
| Celery Beat: deadline reminders (8am UTC) | ✅ Done |
| Celery Beat: at-risk student detection (Sunday 9am) | ✅ Done |
| WebSocket manager: broadcast + per-user push | ✅ Done |

---

## Phase 3 — Advanced Features ✅

| Task | Status |
|---|---|
| Admin dashboard (stats, user list, classroom list) | ✅ Done |
| Profile update endpoint (name, avatar, password) | ✅ Done |
| Similarity flagging + teacher notification | ✅ Done |
| Publish/unpublish toggle on assignments | ✅ Done |
| Role guards: require_teacher, require_student, require_admin | ✅ Done |

---

## Phase 4 — Production Hardening ✅

| Task | Status |
|---|---|
| Frontend lazy loading + bundle splitting (Vite manualChunks) | ✅ Done |
| Scroll restoration on route change | ✅ Done |
| Nginx SPA config + static asset caching | ✅ Done |
| Docker multi-stage build (frontend + backend) | ✅ Done |
| Full-stack docker-compose.yml at project root | ✅ Done |
| GitHub Actions CI (tsc + vite build + ruff + pytest + docker build) | ✅ Done |
| CORS env-var driven (`CORS_ORIGINS` in settings) | ✅ Done |
| VITE_API_URL env support in vite.config.ts | ✅ Done |

---

## Phase 5 — Polish 🔲

| Task | Status |
|---|---|
| Google OAuth (authlib backend + @react-oauth/google frontend) | 🔲 Todo |
| Email notifications (submission confirmed, grade released) | 🔲 Todo |
| File upload (MinIO / S3 for `file_url` on submissions) | 🔲 Todo |
| PDF grade reports (WeasyPrint or Puppeteer) | 🔲 Todo |
| Grade trend charts (recharts / victory) | 🔲 Todo |
| ⌘K command palette | 🔲 Todo |
| Mobile responsive sidebar (drawer on small screens) | 🔲 Todo |
| Prometheus metrics + Grafana dashboard | 🔲 Todo |
| Render / Railway one-click deploy config | 🔲 Todo |

---

## Running Locally

```bash
# 1. Clone and set up env
cp .env.example .env                  # root (just POSTGRES_PASSWORD)
cp backend/.env.example backend/.env  # fill in JWT_SECRET, LLM_API_KEY, etc.

# 2. Start everything
docker compose up --build

# Frontend → http://localhost:80
# API docs  → http://localhost:8000/api/docs
```

### Development (hot-reload)

```bash
# Backend only
cd backend
docker compose -f docker-compose.dev.yml up --build

# Frontend only (separate terminal)
cd frontend
npm install
npm run dev   # http://localhost:3000 — proxies /api to localhost:8000
```
