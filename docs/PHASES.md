# ClassPulse — 5-Phase Implementation Roadmap

> "Google Classroom, but it actually helps you learn — not just submit."

This document describes the complete 5-phase plan to build ClassPulse from a blank repo to a production-ready platform. Each phase is self-contained and produces a working, testable slice of the system.

---

## Phase 0 — Project Setup & Architecture (Current)

**Goal:** Establish the monorepo skeleton, Docker Compose stack, and all configuration so every future phase can start coding, not configuring.

**Deliverables:**
- Full directory structure (backend + frontend + nginx + docs)
- `docker-compose.yml` with all 6 services wired up (api, worker, beat, db, redis, nginx)
- Environment variable contracts (`.env.example`)
- Backend Python project scaffold (`main.py`, `config.py`, `database.py`, router tree, stub modules)
- Frontend React/Vite/TypeScript project scaffold (package.json, Tailwind, all page/component stubs, TypeScript types)
- Nginx reverse proxy config (API routing, WebSocket upgrade, SPA fallback, rate limiting)
- Both documentation files (`PHASES.md`, `PHASE_0.md`)

**Done when:** `docker compose up` starts all 6 containers and `GET /health` returns `{"status": "ok"}`.

---

## Phase 1 — Core MVP (Weeks 1–4)

**Goal:** Deliver the minimum viable product that demonstrates the core innovation — the Draft → AI Feedback → Improve → Final Submit loop.

### Backend
| Area | What gets built |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` — JWT (15 min access + 7 day refresh), bcrypt password hashing, role-based dependency guards (`require_teacher`, `require_admin`) |
| Database | All SQLAlchemy models (User, Classroom, Enrollment, Assignment, RubricCriterion, Submission, AIFeedback, Grade, Notification). Alembic migration `0001_initial`. |
| Classrooms | Full CRUD. Auto-generate 6-char join code. `POST /classrooms/join` for students. Settings JSONB field. |
| Assignments | Create with rubric builder (criteria array). Publish endpoint notifies students. |
| Submissions | `POST /assignments/:id/submit-draft` — validates draft count, queues Celery `generate_ai_feedback` task. `POST /assignments/:id/submit-final` — locks submission, triggers similarity detection. |
| AI Feedback | `generate_ai_feedback` Celery task: builds structured LLM prompt (rubric + submission), parses JSON response, stores per-criterion feedback in `ai_feedback` table. SHA-256 cache in Redis. |
| Grading | `POST /submissions/:id/grade` (rubric click-scoring). `POST /assignments/:id/release-grades`. |
| Dashboard | `GET /dashboard/deadlines` (student). `GET /dashboard/grading-queue` (teacher). |

### Frontend
| Area | What gets built |
|---|---|
| Auth | Login + Register pages. JWT stored in memory + refresh token in `httpOnly` cookie. Axios interceptor for auto-refresh. |
| Routing | React Router v6 with role-aware protected routes (`<StudentRoute>`, `<TeacherRoute>`). |
| Student flow | Dashboard with deadline calendar (color-coded urgency). Classroom page → Assignment page → Submission editor with draft submit → AI feedback panel → final submit. Draft history timeline. |
| Teacher flow | Create classroom → Create assignment with rubric builder (drag-to-reorder criteria). Grading view with rubric click-scoring (Excellent/Good/Average/Poor cards → auto-calculates score). |
| State | Zustand auth store. React Query for all server data. |

**Done when:** A teacher can create a classroom, post an assignment with a rubric, a student can submit a draft and see AI feedback within 30 seconds, and the teacher can grade and release.

---

## Phase 2 — Real-Time & Analytics (Weeks 5–6)

**Goal:** Make the platform feel live — teachers see submissions come in, students get instant notifications.

### Backend
| Area | What gets built |
|---|---|
| WebSocket | `/ws/notifications` endpoint. JWT auth via query param. Subscribes to Redis pub/sub channels: `user:{id}:notifications` and `classroom:{id}:events`. |
| Notification events | `assignment_posted`, `deadline_reminder`, `feedback_ready`, `grade_released`, `submission_count` (teacher only). |
| Celery Beat | `send_deadline_reminders` — hourly job, queries assignments with deadline in next 24h and 1h, creates notifications for students who haven't submitted. |
| Dashboard analytics | `GET /dashboard/grade-trends` (student: line chart data per classroom). `GET /classrooms/:id/analytics` (teacher: avg score, score distribution histogram, topic-wise performance from rubric criterion names). `GET /dashboard/at-risk` (teacher: rolling average below threshold). |
| Submission tracker | WebSocket pushes `submission_count` update to teacher whenever a student submits. |

### Frontend
| Area | What gets built |
|---|---|
| WebSocket hook | `useWebSocket` — connects on login, reconnects with exponential backoff, dispatches events to Zustand notification store. |
| Notification bell | Badge count. Dropdown list with mark-as-read. Toast for incoming real-time events. |
| Grade trends | Recharts `LineChart` on student dashboard. Per-subject line + overall GPA trend. |
| Teacher analytics | Score distribution `BarChart`. Live submission counter "45/60 submitted". At-risk student list. |
| Deadline calendar | Color-coded urgency in student dashboard (red <24h, orange <3 days, green >3 days). |

**Done when:** Teacher opens grading view and sees submission count increment in real-time. Student receives a toast notification when grade is released.

---

## Phase 3 — Advanced Features (Weeks 7–8)

**Goal:** Add the power features that make ClassPulse defensible — bulk tools, academic integrity, and admin visibility.

### Backend
| Area | What gets built |
|---|---|
| Similarity detection | `detect_similarity` Celery task (triggered on final submit). Computes TF-IDF vectors for all final submissions in an assignment. Flags pairs with cosine similarity > 0.85. Stores in `similarity_flags` table. |
| Bulk feedback | `POST /assignments/:id/bulk-feedback` — teacher writes feedback once, selects N student submission IDs, applies to all. |
| At-risk detection | `detect_at_risk_students` Celery Beat daily task. Queries rolling 5-assignment average < configurable threshold. Stores flags for teacher dashboard. |
| PDF reports | `generate_report_pdf` on-demand task. ReportLab: student report card (all assignments, scores, trend chart). Teacher: class performance summary. |
| Admin dashboard | `GET /admin/classrooms` (all classrooms in department). `GET /admin/analytics` (grading turnaround time, assignment frequency, at-risk count across dept). |
| File uploads | Multipart form upload for file-type assignments. Store locally in dev, S3 in production. Max 10MB enforced by Nginx. |

### Frontend
| Area | What gets built |
|---|---|
| Similarity flags | Teacher grading view: flag icon on submissions with similarity alerts. Shows which other student's submission it matched. |
| Bulk feedback modal | Multi-select submissions → write shared feedback → apply. |
| PDF download | "Download Report" button triggers on-demand Celery task, polls for completion, downloads PDF. |
| Admin dashboard | Department-wide view: faculty list with assignment/grading stats, at-risk count, turnaround leaderboard. |
| File submission | File upload dropzone in submission editor. Shows file name + size. |

**Done when:** Teacher can flag similar submissions, apply bulk feedback to 20 students in one click, and download a class PDF report.

---

## Phase 4 — Production Hardening & Deployment (Week 9)

**Goal:** Make the system safe, observable, and deployable to real infrastructure.

### Backend
| Area | What gets built |
|---|---|
| Security | Input sanitization on all text fields (bleach/markupsafe). File type validation (python-magic, not just extension). CSRF protection. Rate limiting via Redis sliding window (LLM calls: 5/student/hour, auth: 10/IP/min). |
| Testing | pytest suite: unit tests for services (mocked DB), integration tests for all API endpoints (real test DB). CI passes before merge. Target: 80% coverage on core paths. |
| Observability | Structured JSON logging (loguru). Request ID middleware. Celery task success/failure logging. Basic Prometheus metrics endpoint (`/metrics`). |
| Database | Connection pooling tuned (20 connections). Index audit — verify all FK columns and frequent query columns are indexed. |
| Deployment | `docker-compose.prod.yml` with resource limits, health checks, restart policies. Nginx SSL termination config (Let's Encrypt). Deploy to Render (free tier for demo) or AWS EC2 t3.small. |
| CI/CD | GitHub Actions workflow: lint → test → build Docker image → push to registry → deploy. |

### Frontend
| Area | What gets built |
|---|---|
| Error boundary | Global React error boundary with fallback UI. |
| Loading states | Skeleton screens for all list views (no raw spinners). |
| Offline handling | Toast when WebSocket disconnects. Retry logic. |
| Accessibility | ARIA labels on interactive elements. Keyboard navigation for rubric click-grader. |
| Build optimization | Code splitting by route. Bundle analysis. Target: < 200KB initial JS. |

**Done when:** `docker compose -f docker-compose.prod.yml up` on a VPS serves the app over HTTPS with all 6 containers healthy.

---

## Phase 5 — Polish & Monitoring (Week 10+)

**Goal:** Production operations, UX refinements based on real usage, and extended features.

### Areas
| Area | What gets built |
|---|---|
| Monitoring | Grafana + Prometheus dashboard: API p95 latency, Celery queue depth, AI feedback generation time, WebSocket connection count. Alert when AI feedback task backlog > 50. |
| Email notifications | FastAPI-Mail integration: deadline reminders via email (fallback when WebSocket disconnected). Welcome email on registration. |
| Mobile responsiveness | Audit and fix all pages on 375px viewport. Priority: student submission flow + deadline calendar. |
| Dark mode | Tailwind `dark:` variant throughout. System preference detection. |
| Markdown preview | Split-pane editor for assignment description (teacher) and submission text (student) — live preview. |
| AI improvements | Per-assignment feedback tone config (strict/balanced/encouraging). Teacher can add custom instructions appended to system prompt. |
| Google OAuth | `POST /auth/google` — OAuth 2.0 PKCE flow. Maps Google email to existing account or creates new. |
| Data export | Teacher: export all grades for an assignment as CSV. Admin: full department export. |
| Internationalization | i18n scaffolding (react-i18next). English + Hindi string files as starting point. |

**Done when:** Platform is running in production with real users, monitored, and maintainable by the team.

---

## Summary Table

| Phase | Focus | Key Milestone |
|---|---|---|
| 0 | Setup & Architecture | `docker compose up` — all 6 services healthy |
| 1 | Core MVP | Student submits draft → AI feedback in <30s → teacher grades |
| 2 | Real-Time & Analytics | Live submission count + WebSocket notifications |
| 3 | Advanced Features | Similarity detection + bulk feedback + PDF reports |
| 4 | Production & Deployment | HTTPS deploy on real VPS with CI/CD |
| 5 | Polish & Monitoring | Grafana dashboard, email fallback, mobile UX |
