<div align="center">

# ClassPulse

### The classroom platform that grades with you, not after you.

Students submit drafts and get **instant, rubric-aligned AI feedback** before the deadline.
Teachers grade in half the time with **AI-suggested scores** and **real-time plagiarism flags**.

[![CI](https://github.com/sumanthd032/ClassPulse/actions/workflows/ci.yml/badge.svg)](https://github.com/sumanthd032/ClassPulse/actions/workflows/ci.yml)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)
![Python](https://img.shields.io/badge/Python_3.11-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-violet)

[Quick Start](#-quick-start) · [How It Works](#-the-core-loop) · [Architecture](#-architecture) · [API](#-api)

</div>

---

## 🎯 The Core Loop

Most platforms only see student work **once** — after the deadline, when it's too late to learn anything. ClassPulse closes the loop *before* submission.

```
   ┌─────────┐   draft    ┌──────────────┐   feedback   ┌─────────┐
   │ Student │ ─────────▶ │  Gemini AI   │ ───────────▶ │ Student │
   │         │            │  reads the   │   per rubric │ revises │
   │         │ ◀───────── │   rubric     │   criterion  │         │
   └─────────┘            └──────────────┘              └────┬────┘
        │                                                    │ final
        │            ┌──────────────────────────┐           │
        └──────────▶ │ TF-IDF plagiarism scan +  │ ◀─────────┘
                     │ AI-suggested grade for the │
                     │        teacher             │
                     └──────────────────────────┘
```

1. **Submit a draft.** A Celery worker sends it to Gemini, which scores every rubric criterion and writes targeted feedback — in seconds.
2. **Revise and resubmit.** Up to *N* drafts before the deadline. The student improves; the teacher does nothing.
3. **Final submission triggers a plagiarism scan.** Every final is compared against the cohort; pairs above 80% cosine similarity flag the teacher in real time over WebSocket.
4. **Teacher grades fast.** AI pre-fills a suggested level and marks per criterion. The teacher accepts, tweaks, or overrides — then releases grades to the class.

---

## ✨ What You Get

<table>
<tr>
<td width="33%" valign="top">

### 👩‍🎓 Students
- Instant AI feedback on every draft
- A clear rubric breakdown, not just a number
- File attachments on submissions
- Live notifications when grades drop
- Personal grade-trend charts

</td>
<td width="33%" valign="top">

### 👨‍🏫 Teachers
- AI-suggested scores per criterion
- Real-time plagiarism alerts
- Full gradebook → one-click PDF export
- Classroom analytics & at-risk detection
- Stream, materials, topics, comments

</td>
<td width="33%" valign="top">

### 🛡️ Admins / HOD
- Platform-wide analytics
- User & classroom oversight
- Role-based access control
- Automated weekly at-risk reports

</td>
</tr>
</table>

> **Always-on automation** — Celery Beat applies late penalties at midnight, fires deadline reminders at 8am, and runs at-risk detection weekly. **No cron cowboy required.**

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (React)                      │
│  Vite · Tailwind · Zustand · React Query · Framer Motion │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP /api  +  WS /ws
┌───────────────────▼─────────────────────────────────────┐
│                  FastAPI  (uvicorn)                      │
│  Auth · Classrooms · Assignments · Submissions           │
│  Grading · Notifications · Dashboard · Admin             │
└───────┬──────────────────┬──────────────────┬───────────┘
        │ SQLAlchemy async  │ Redis pub/sub    │ S3 API
┌───────▼────────┐  ┌───────▼──────────┐  ┌────▼───────────┐
│  PostgreSQL 16 │  │     Redis 7      │  │     MinIO      │
│   (all data)   │  │ broker · tokens  │  │ file storage   │
└────────────────┘  └───────┬──────────┘  └────────────────┘
                            │ Celery tasks
                 ┌──────────▼──────────────────────┐
                 │         Celery Workers           │
                 │  AI feedback · Similarity check  │
                 │  Late penalties · Reminders      │
                 └─────────────────────────────────┘
```

**Stack** — React 18 · TypeScript · FastAPI · Python 3.11 · SQLAlchemy (async) · Pydantic v2 · PostgreSQL 16 · Redis 7 · MinIO · Celery · Google Gemini (`gemini-2.5-flash`) · Docker.

---

## 🚀 Quick Start

**Prerequisites:** Docker + Docker Compose, and a [Google AI Studio](https://aistudio.google.com/) (Gemini) API key.

```bash
git clone https://github.com/sumanthd032/ClassPulse.git
cd ClassPulse
cp backend/.env.example backend/.env
```

Set two values in `backend/.env` (everything else has working local defaults):

```env
JWT_SECRET=<run: python -c "import secrets; print(secrets.token_hex(32))">
LLM_API_KEY=<your Gemini API key>
```

Then bring up the whole stack:

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3001 |
| API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/api/docs |

First build takes ~3 min; after that it's cached and starts in seconds.

<details>
<summary><b>Hot-reload dev setup (run backend & frontend separately)</b></summary>

```bash
# Backend — db + redis + migrate + api(--reload) + worker + beat
cd backend
cp .env.example .env          # set JWT_SECRET + LLM_API_KEY
docker compose -f docker-compose.dev.yml up --build
# Postgres → localhost:5433, Redis → localhost:6380

# Frontend — Vite proxies /api and /ws to :8000 automatically
cd frontend
npm install
npm run dev                   # http://localhost:3000
```

</details>

---

## 📡 API

Interactive Swagger UI lives at `/api/docs`. The endpoints that carry the product:

| Method | Path | What it does |
|---|---|---|
| `POST` | `/api/v1/assignments/{id}/drafts` | Submit a draft → triggers AI feedback |
| `POST` | `/api/v1/assignments/{id}/final` | Submit final → triggers plagiarism scan |
| `POST` | `/api/v1/submissions/{id}/grade` | Grade a submission (teacher) |
| `GET` | `/api/v1/assignments/{id}/gradebook` | Full grade matrix |
| `GET` | `/api/v1/assignments/{id}/gradebook/pdf` | Download gradebook as PDF |
| `POST` | `/api/v1/classrooms/join` | Join a classroom by code |
| `GET` | `/api/v1/me/dashboard` | Role-aware dashboard stats |
| `WS` | `/ws?token=<jwt>` | Real-time notification stream |

---

## 📂 Project Layout

```
ClassPulse/
├── backend/                 # FastAPI service
│   ├── app/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic v2 request/response
│   │   ├── routers/         # Route handlers
│   │   ├── services/        # Business logic (pure async)
│   │   ├── workers/         # Celery tasks (AI, plagiarism, cron)
│   │   └── utils/           # Security, LLM client, MinIO, WebSockets
│   └── alembic/             # Database migrations
├── frontend/                # React + Vite SPA
│   └── src/
│       ├── api/             # Typed API clients (one per domain)
│       ├── components/      # UI primitives, layout, charts, ⌘K palette
│       ├── pages/           # Route-level screens
│       ├── stores/          # Zustand state
│       └── hooks/           # useAuth, useWebSocket
└── docker-compose.yml       # Full-stack, production-like
```

---

## 📄 License

[MIT](LICENSE) © 2026 Sumanth D
