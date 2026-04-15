<div align="center">

# ⚡ ClassPulse

**AI-powered classroom management for engineering colleges.**  
Students submit drafts and get instant LLM feedback before the deadline. Teachers grade faster with AI-suggested scores and real-time plagiarism flags.

[![CI](https://github.com/your-username/ClassPulse/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/ClassPulse/actions/workflows/ci.yml)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-violet)

[**Live Demo**](#) · [**API Docs**](#api-documentation) · [**Report Bug**](https://github.com/your-username/ClassPulse/issues)

</div>

---

## ✨ What Makes ClassPulse Different

| Feature | Description |
|---|---|
| **Draft → Feedback Loop** | Students submit up to N drafts before the deadline. Each draft triggers instant AI feedback aligned to the grading rubric. |
| **Rubric-Aligned AI Grading** | Google Gemini scores each rubric criterion independently, suggesting a level (excellent / good / average / poor) and estimated marks. |
| **TF-IDF Plagiarism Detection** | Runs on every final submission. Flags pairs with >80% cosine similarity and notifies the teacher in real-time via WebSocket. |
| **Real-Time Notifications** | WebSocket push for grade releases, new assignments, plagiarism flags, and deadline reminders. |
| **Role-Based Access** | Three roles — **Student**, **Teacher**, **Admin/HOD** — each with their own dashboard and permissions. |
| **Celery Beat Automation** | Automatic late penalties (midnight UTC), deadline reminders (8am), and at-risk student detection (weekly). |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (React)                      │
│  Vite · Tailwind · Zustand · React Query · Framer Motion│
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP /api  +  WS /ws
┌───────────────────▼─────────────────────────────────────┐
│                  FastAPI  (uvicorn)                       │
│  Auth · Classrooms · Assignments · Submissions           │
│  Grading · Notifications · Dashboard · Admin             │
└───────┬─────────────────────────┬───────────────────────┘
        │ SQLAlchemy async        │ Redis pub/sub
┌───────▼──────────┐    ┌────────▼────────────────────────┐
│  PostgreSQL 16   │    │           Redis 7                │
│  (all data)      │    │  tokens · rate-limits · broker   │
└──────────────────┘    └──────────┬──────────────────────┘
                                   │ Celery tasks
                        ┌──────────▼──────────────────────┐
                        │         Celery Workers            │
                        │  AI feedback · Similarity check  │
                        │  Late penalties · Reminders       │
                        └─────────────────────────────────-┘
```

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- A [Google AI Studio](https://aistudio.google.com/) API key (Gemini)

### 1 — Clone & configure

```bash
git clone https://github.com/your-username/ClassPulse.git
cd ClassPulse

# Backend environment (required)
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in:

```env
JWT_SECRET=<random 32+ char string>
LLM_API_KEY=<your Gemini API key>
```

Everything else has working defaults for local development.

### 2 — Start the full stack

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| **Frontend** | http://localhost:3001 |
| **API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/api/docs |

First build takes ~3 minutes (downloads images and wheels). Subsequent builds are cached and start in seconds.

---

## 🛠️ Development (hot-reload)

Run backend and frontend separately for the best developer experience.

### Backend

```bash
cd backend
cp .env.example .env   # fill in secrets

# Start only db + redis + migrate + api (with --reload)
docker compose -f docker-compose.dev.yml up --build
```

Backend hot-reloads on every file save. Postgres exposed on `localhost:5433`, Redis on `localhost:6380`.

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

Vite proxies `/api` → `localhost:8000` and `/ws` → `ws://localhost:8000` automatically.

---

## 📁 Project Structure

```
ClassPulse/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic v2 request/response schemas
│   │   ├── routers/         # FastAPI route handlers
│   │   ├── services/        # Business logic (pure async functions)
│   │   ├── workers/         # Celery tasks (AI, plagiarism, cron)
│   │   └── utils/           # Security, LLM client, WebSocket manager
│   ├── alembic/             # Database migrations
│   ├── Dockerfile
│   ├── docker-compose.dev.yml
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/             # Axios API clients (one file per domain)
│   │   ├── components/      # UI primitives + layout + notifications
│   │   ├── hooks/           # useAuth, useWebSocket
│   │   ├── pages/           # Route-level page components
│   │   ├── stores/          # Zustand state (auth, notifications)
│   │   └── types/           # TypeScript interfaces
│   ├── Dockerfile
│   ├── nginx.conf
│   └── vite.config.ts
│
├── docs/
│   └── PHASES.md            # Phase completion tracker
│
├── .github/
│   └── workflows/ci.yml     # GitHub Actions CI
│
├── docker-compose.yml       # Full-stack production-like compose
└── README.md
```

---

## 🔌 API Documentation

Interactive Swagger UI is available at `/api/docs` when running locally.

### Key Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Get JWT tokens |
| `PATCH` | `/api/v1/auth/me` | Update profile / change password |
| `GET` | `/api/v1/classrooms` | List enrolled / owned classrooms |
| `POST` | `/api/v1/classrooms` | Create classroom (teacher) |
| `POST` | `/api/v1/classrooms/join` | Join classroom with code (student) |
| `POST` | `/api/v1/classrooms/{id}/assignments` | Create assignment + rubric |
| `POST` | `/api/v1/assignments/{id}/drafts` | Submit draft → triggers AI feedback |
| `POST` | `/api/v1/assignments/{id}/final` | Submit final → triggers plagiarism check |
| `POST` | `/api/v1/submissions/{id}/grade` | Grade a submission (teacher) |
| `GET` | `/api/v1/me/dashboard` | Role-aware dashboard stats |
| `GET` | `/api/v1/admin/stats` | Platform-wide analytics (admin) |
| `WS` | `/ws?token=<jwt>` | Real-time notifications |

---

## 🧪 Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

> Tests require a running PostgreSQL and Redis. Use the dev compose to spin them up first.

---

## 🚢 Deploying to Production

1. **Set `CORS_ORIGINS`** in `backend/.env` to your production frontend domain.
2. **Set a strong `JWT_SECRET`** (min 32 random chars).
3. Build and push images:
   ```bash
   docker compose build
   docker compose push
   ```
4. Deploy on [Render](https://render.com), [Railway](https://railway.app), or any Docker host using `docker-compose.yml`.

---

## 🗺️ Roadmap

- [ ] Google OAuth (student/teacher SSO)
- [ ] File upload submissions (MinIO / S3)
- [ ] PDF grade reports per student
- [ ] Grade trend charts (recharts)
- [ ] Mobile-responsive sidebar
- [ ] Email notifications (submission confirmed, grade released)
- [ ] ⌘K command palette
- [ ] Prometheus + Grafana monitoring

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push and open a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## 📄 License

MIT © 2026 Sumanth D

---

<div align="center">
Built with FastAPI · React · PostgreSQL · Redis · Celery · Google Gemini
</div>
