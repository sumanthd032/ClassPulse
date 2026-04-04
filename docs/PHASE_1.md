# Phase 1 — Core MVP

> Goal: Build the minimum viable product that demonstrates ClassPulse's core innovation — the **Draft → AI Feedback → Improve → Final Submit** loop.

This document explains **what** was built, **why** each decision was made, and **how** the code works. Read it alongside the source files.

---

## What Was Built (Summary)

| Step | Area | Files |
|---|---|---|
| 1 | SQLAlchemy Models + Alembic | `backend/app/models/`, `backend/migrations/` |
| 2 | Auth (JWT + bcrypt) | `core/security.py`, `core/exceptions.py`, `dependencies.py`, `api/v1/auth.py`, `schemas/user.py` |
| 3 | Classrooms | `schemas/classroom.py`, `services/classroom_service.py`, `api/v1/classrooms.py` |
| 4 | Assignments + Rubric | `schemas/assignment.py`, `services/assignment_service.py`, `api/v1/assignments.py` |
| 5 | Submissions + AI Feedback | `schemas/submission.py`, `services/llm_service.py`, `workers/tasks/ai_feedback.py`, `services/submission_service.py`, `api/v1/submissions.py` |
| 6 | Grading + Dashboard | `schemas/grade.py`, `services/grading_service.py`, `api/v1/grading.py`, `api/v1/dashboard.py` |
| 7 | Frontend | `src/api/`, `src/store/`, `src/pages/`, `src/components/` |

---

## Step 1 — SQLAlchemy Models + Alembic Migration

### What?
SQLAlchemy ORM models are Python classes that map to database tables. Each model class represents one table.

### Why SQLAlchemy 2.0 instead of raw SQL?
- **Type safety**: `Mapped[uuid.UUID]` and `mapped_column()` give full IDE support and catch type errors at write time.
- **Migrations**: Alembic (SQLAlchemy's migration tool) tracks schema changes and applies them in order — like git for your database.
- **Async support**: SQLAlchemy 2.0 with `asyncpg` driver supports fully async DB operations, matching FastAPI's async nature.

### How — Model structure
```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    ...
```
- `Base` comes from `database.py` (`DeclarativeBase`) — all models inherit from it.
- `Mapped[T]` is a type hint that SQLAlchemy 2.0 uses for column mapping. The actual column definition is in `mapped_column(...)`.
- `UUID(as_uuid=True)` tells asyncpg to work with Python `uuid.UUID` objects, not raw strings.
- `index=True` on `email` creates a B-tree index in PostgreSQL — makes `WHERE email = ?` fast.

### How — JSONB columns
```python
settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=lambda: {
    "max_drafts": 3,
    "late_policy": "penalty",
    "ai_feedback": True,
})
```
`JSONB` is PostgreSQL's binary JSON format — it stores JSON but is indexable and queryable with operators like `@>` (contains). We use it for `settings` (classroom config) and `levels` (rubric criterion descriptors) because these fields have flexible structure.

### How — Partial unique index
```python
# In the migration:
op.execute(
    "CREATE UNIQUE INDEX uq_final_submission ON submissions (assignment_id, student_id) "
    "WHERE is_final = true"
)
```
A **partial unique index** enforces uniqueness only for rows matching `WHERE is_final = true`. This allows a student to have multiple draft submissions (is_final = false) but only one final submission per assignment — the database itself enforces this constraint, not just application code.

### How — Alembic env.py
```python
# env.py key lines:
from app.config import settings
from app.database import Base
import app.models   # registers all models with Base.metadata

config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(...)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
```
Alembic needs to:
1. Know the database URL (read from `.env` via `settings`).
2. Know which tables exist (by importing all models so `Base.metadata` is populated).
3. Use async-compatible connection (asyncpg requires `asyncio.run()`).

**To run a migration:**
```bash
cd backend
alembic upgrade head          # apply all pending migrations
alembic downgrade -1          # roll back one migration
alembic revision --autogenerate -m "add column X"  # generate new migration from model changes
```

---

## Step 2 — Authentication

### What?
- `POST /auth/register` — create account, return JWT tokens
- `POST /auth/login` — verify password, return tokens
- `POST /auth/refresh` — exchange refresh token for new access token
- `GET /auth/me` — return current user

### Why JWT (JSON Web Tokens) instead of sessions?
Sessions require the server to store session state (in Redis or DB). JWTs are **stateless** — the token itself contains all the information needed (user ID, role, expiry). The server only needs its secret key to verify the token.

**Trade-off**: JWTs can't be revoked before expiry (unlike sessions). We mitigate this with short expiry (15 min) + refresh tokens (7 days). If you need revocation, store a token blacklist in Redis.

### How — bcrypt password hashing
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)   # generates: $2b$12$<salt><hash>

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)  # constant-time comparison
```
**Why bcrypt?** It's intentionally slow (configurable cost factor). This means brute-force attacks must spend real compute time per guess. MD5/SHA256 are fast, which makes them bad for passwords. bcrypt generates a random salt automatically — two users with the same password get different hashes.

### How — Timing-safe login
```python
dummy_hash = "$2b$12$dummyhashfortimingprotectiononly.....AAAAAAAAA"
stored_hash = user.password_hash if user else dummy_hash
if not verify_password(body.password, stored_hash) or user is None:
    raise UnauthorizedError("Invalid email or password.")
```
If we returned immediately when the email doesn't exist, an attacker could measure response times to determine which emails are registered (timing attack). By always calling `verify_password` (even with a dummy hash when the user doesn't exist), response time is the same regardless.

### How — JWT token creation
```python
def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = {"sub": user_id, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
```
- `sub` = subject — standard JWT claim for "who this token is for"
- `exp` = expiry — `python-jose` validates this automatically on decode
- `type` = distinguishes access from refresh tokens (prevents using a refresh token as an access token)
- `HS256` = HMAC-SHA256 — uses a shared secret. For multi-service systems, use RS256 (asymmetric).

### How — FastAPI dependency injection
```python
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DbSession,
) -> User:
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    return result.scalar_one_or_none()
```
FastAPI's `Depends()` builds a dependency graph. When a route declares `current_user: CurrentUser`, FastAPI:
1. Calls `bearer_scheme` to extract the Authorization header.
2. Calls `get_current_user` with the extracted token + a DB session.
3. Injects the returned `User` object into the route handler.

This means every protected route gets the authenticated user without any boilerplate.

---

## Step 3 — Classrooms

### What?
- Create classroom (teacher only) with auto-generated 6-char join code
- List all classrooms the user is in
- Join a classroom by code (any authenticated user)
- Update classroom settings

### How — Join code generation
```python
def _generate_join_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=6))
```
36 possible characters, 6 positions = 36^6 = ~2.1 billion combinations. Collision probability is negligible but we still retry up to 5 times if a collision occurs (defensive programming).

### How — Service layer pattern
```
Route handler → Service function → Database
```
Route handlers only:
1. Extract validated data from the request.
2. Call a service function.
3. Return the result.

All business logic lives in the service. This makes the service testable without a real HTTP request — you just call `classroom_service.create_classroom(db, teacher, data)` directly in tests.

### How — Auto-enroll creator
```python
enrollment = Enrollment(
    user_id=teacher.id,
    classroom_id=classroom.id,
    role=EnrollmentRole.co_teacher,
)
```
When a teacher creates a classroom, they're automatically enrolled as `co_teacher`. This means the classroom appears in their `GET /classrooms` response (which queries the `enrollments` table).

---

## Step 4 — Assignments + Rubric Builder

### What?
- Create assignment with rubric criteria (teacher only)
- Each criterion has: name, max_marks, and 4 level descriptors (excellent/good/average/poor)
- Publish assignment (makes it visible to students)

### How — Rubric stored as multiple rows, not JSON
```python
# Each criterion is a separate database row in rubric_criteria table
criterion = RubricCriterion(
    assignment_id=assignment.id,
    name=c["name"],
    max_marks=c["max_marks"],
    order_index=idx,
    levels=c["levels"],   # JSONB: {excellent: "...", good: "...", ...}
)
```
**Why separate rows instead of one JSONB array on the assignment?**
- Each criterion needs its own UUID so `ai_feedback` and `grades` can reference `criterion_id`.
- Separate rows allow us to query "what's the feedback for criterion X?" without parsing a JSON array.
- JSONB is used only for `levels` (the descriptors) which are always read together as a unit.

### How — `await db.flush()` vs `await db.commit()`
```python
db.add(assignment)
await db.flush()   # ← sends INSERT to DB, gets assignment.id, but doesn't commit

for c in criteria:
    criterion = RubricCriterion(assignment_id=assignment.id, ...)  # need assignment.id!
    db.add(criterion)

await db.commit()  # ← commits everything atomically
```
`flush()` sends the SQL to the database but doesn't commit. This gives us the auto-generated `assignment.id` (needed as FK for criteria) while keeping everything in one transaction. If anything fails, the entire transaction rolls back.

---

## Step 5 — Submissions + AI Feedback (Core Innovation)

### What?
- Submit draft → validate → create Submission row → enqueue Celery AI feedback task
- AI feedback task → LLM call → store per-criterion feedback → publish Redis event
- Submit final → lock submission (no more edits)
- Fetch all drafts with AI feedback (student view)

### How — Why Celery for AI feedback?
```
Without Celery (synchronous):
  POST /submit-draft
    → FastAPI calls OpenAI API (takes 5-30 seconds)
    → Student waits with a loading spinner
    → Response finally returns

With Celery (asynchronous):
  POST /submit-draft
    → FastAPI creates Submission, pushes task to Redis queue
    → FastAPI returns 201 in <50ms ✓
    → [background] Celery worker calls OpenAI API
    → [background] Worker stores feedback, publishes Redis event
    → [Phase 2] WebSocket pushes "feedback_ready" to student
```

### How — Celery task with asyncio bridge
```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def generate_ai_feedback(self, submission_id: str):
    asyncio.run(_async_generate_feedback(self, submission_id))

async def _async_generate_feedback(task, submission_id: str):
    # async DB calls, async LLM call, async Redis publish
```
Celery tasks are synchronous Python functions. Our DB driver (asyncpg) and LLM client (openai) are async. We bridge them with `asyncio.run()`. The async function creates its own DB engine because Celery workers are separate processes — they can't share the main app's engine.

### How — LLM prompt design
```
System prompt: "You are an academic feedback assistant. Evaluate student submissions against a rubric.
For each criterion, provide: estimated_score, strengths, improvements, suggested_level.
Output ONLY valid JSON."

User message:
RUBRIC:
Criterion 1: Normalization (max 10 marks)
  criterion_id: <uuid>
  Excellent: Correctly identifies all normal forms with examples
  Good: Identifies most normal forms...
  ...

STUDENT SUBMISSION:
The ER diagram shows entities for Patient, Doctor, and Appointment...
```
**Why `temperature=0.3`?** Lower temperature = more deterministic output. For feedback generation, we want consistent, structured JSON — not creative variation.

**Why `response_format={"type": "json_object"}`?** OpenAI's JSON mode guarantees the response is valid JSON. Without it, the LLM might include extra text before/after the JSON.

### How — Redis caching
```python
def _cache_key(content: str, rubric_id: str) -> str:
    return "llm_cache:" + hashlib.sha256(f"{rubric_id}:{content}".encode()).hexdigest()
```
If a student submits identical content twice (or two students submit identical answers), we return cached feedback instead of calling the LLM again. The cache key is a SHA-256 hash of `rubric_id + content`. TTL = 1 hour.

### How — Rate limiting (sliding window)
```python
key = f"llm_rate:{student_id}"
count = await redis_client.incr(key)
if count == 1:
    await redis_client.expire(key, 3600)
return count <= 5   # max 5 calls per hour
```
`INCR` is atomic in Redis — even with concurrent requests, each student gets an accurate count. The TTL is set only on the first call (when count becomes 1). **Limitation**: this isn't a perfect sliding window — it's more like a fixed window that resets after 1 hour from the first call. A true sliding window needs a sorted set. For Phase 1, this is sufficient.

### How — Idempotent task (safe to retry)
```python
# Delete old feedback before inserting new (idempotent — safe if task runs twice)
await db.execute(delete(AIFeedback).where(AIFeedback.submission_id == uuid.UUID(submission_id)))
# Then insert fresh feedback
```
If the task fails after the LLM call but before storing results (network blip), Celery retries it. Without the delete-first pattern, we'd get duplicate feedback rows. With it, re-running the task is safe.

---

## Step 6 — Grading + Dashboard

### What?
- Teacher grades submissions criterion-by-criterion (click Excellent/Good/Average/Poor)
- Score auto-calculates: Excellent=100%, Good=75%, Average=50%, Poor=25% of max_marks
- Release grades (batch operation — all students see results at once)
- Student dashboard: upcoming deadlines with urgency colors
- Teacher dashboard: grading queue (assignments needing grading, count of graded vs ungraded)

### How — Re-gradeable grading
```python
# Delete existing grades first (allows teacher to adjust grades)
await db.execute(delete(Grade).where(Grade.submission_id == submission_id))
# Insert new grades
for g in grades_data:
    grade = Grade(submission_id=..., criterion_id=..., score=..., level=..., ...)
    db.add(grade)
```
Teachers can re-grade a submission before releasing. After release (`is_released=True`), grades become visible to students. We don't lock grades after release in Phase 1 — a teacher could technically re-grade and re-release.

### How — Batch grade release
```python
result = await db.execute(
    update(Grade)
    .where(Grade.submission_id.in_(sub_ids), Grade.is_released == False)
    .values(is_released=True)
    .returning(Grade.id)
)
```
Single SQL `UPDATE ... WHERE ... RETURNING` — atomically flips all ungraded submissions to released. No Python loop needed. The `RETURNING` clause gives us the count of affected rows.

### How — Deadline urgency (dashboard)
```python
hours = diff.total_seconds() / 3600
if hours < 0:    urgency = "red"    # past due
elif hours < 24: urgency = "red"    # < 24 hours
elif hours < 72: urgency = "orange" # < 3 days
else:            urgency = "green"  # > 3 days
```
The frontend maps these to Tailwind colors. The dashboard is refetched every 60 seconds (React Query `refetchInterval`) so colors update as time passes.

---

## Step 7 — Frontend

### Tech Choices Explained

**React Query (`@tanstack/react-query`) for server state:**
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ["deadlines"],       // unique cache key
  queryFn: dashboardApi.deadlines,
  refetchInterval: 60_000,       // auto-refetch every 60s
});
```
React Query handles: caching, background refetching, loading/error states, deduplication (if two components use the same queryKey, only one request is made). We don't need to write `useEffect` + `useState` + error handling for every API call.

**Zustand for client state:**
```typescript
const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      ...
    }),
    { name: "classpulse-auth", partialize: (s) => ({ user: s.user, refreshToken: s.refreshToken }) }
  )
);
```
`persist` middleware saves selected state to `sessionStorage`. We only persist `user` and `refreshToken` — the access token is re-acquired from the refresh token on page load. This means even after a browser refresh, the user stays logged in.

**React Hook Form + Zod for forms:**
```typescript
const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8),
});

const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(schema),
});
```
- `register("email")` attaches `name`, `onChange`, `onBlur`, `ref` to the input.
- Zod schema runs on submit (not on every keystroke) → no jank.
- `formState.errors.email.message` gives you the exact error string.

**Axios interceptor for silent token refresh:**
```typescript
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !original._retry) {
      // Refresh the access token, retry the original request
    }
  }
);
```
When the access token expires (15 min), the next API call gets a 401. The interceptor:
1. Calls `POST /auth/refresh` with the refresh token.
2. Updates the Zustand store with the new access token.
3. Retries the original request with the new token.
4. **Queues** other in-flight requests during the refresh (avoids calling `/refresh` multiple times simultaneously).

The user never sees an error — they just continue using the app.

### Page Architecture

**AssignmentPage (student) — the core loop:**
```typescript
// Poll every 5 seconds for AI feedback (until feedback arrives)
const { data: submissions } = useQuery({
  queryKey: ["my-submissions", assignmentId],
  queryFn: () => submissionsApi.mySubmissions(assignmentId!),
  refetchInterval: 5000,  // ← polling
});
```
Why polling instead of WebSocket in Phase 1? Phase 2 adds WebSocket. In Phase 1, polling every 5 seconds is simple and reliable. The UI shows "Generating feedback..." until the `ai_feedback` array is non-empty.

**GradingPage (teacher) — click-to-grade:**
```typescript
const LEVEL_MULTIPLIERS = { excellent: 1.0, good: 0.75, average: 0.5, poor: 0.25 };

const setLevel = (submissionId, criterionId, level, maxMarks) => {
  const score = Math.round(maxMarks * LEVEL_MULTIPLIERS[level]);
  // Update local state — batch submit with "Save Grades" button
};
```
Grades are stored in local React state as the teacher clicks. The "Save Grades" button sends a single `POST /submissions/:id/grade` with all criteria at once. This avoids a DB write for every click.

**ProtectedRoute — role-based access:**
```typescript
function ProtectedRoute({ children, allowedRoles }) {
  if (!isAuthenticated()) return <Navigate to="/login" />;
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={user.role === "teacher" ? "/teacher" : "/student"} />;
  }
  return children;
}
```
Two levels of protection: (1) must be logged in, (2) must have the right role. A student trying to access `/teacher` gets redirected to `/student`, not an error page.

---

## How to Run Phase 1 Locally

```bash
# 1. Start DB + Redis
docker compose up db redis -d

# 2. Copy env and configure
cp .env.example .env
# Edit .env: set JWT_SECRET and LLM_API_KEY

# 3. Run migrations
cd backend
pip install -r requirements.txt
alembic upgrade head

# 4. Start API (hot reload)
uvicorn app.main:app --reload

# 5. Start Celery worker (new terminal)
celery -A app.workers.celery_app worker --loglevel=info

# 6. Start frontend (new terminal)
cd ../frontend
npm install
npm run dev   # → http://localhost:5173
```

Or run everything with Docker:
```bash
docker compose up --build
```

---

## Key Files Reference

| File | Purpose |
|---|---|
| `backend/app/models/__init__.py` | Import all models — required for Alembic to detect them |
| `backend/migrations/env.py` | Alembic async configuration |
| `backend/migrations/versions/0001_initial_schema.py` | Full schema with indexes |
| `backend/app/core/security.py` | bcrypt + JWT — no framework coupling |
| `backend/app/dependencies.py` | `get_db`, `get_current_user`, `require_teacher` |
| `backend/app/services/llm_service.py` | LLM prompt, caching, rate limiting |
| `backend/app/workers/tasks/ai_feedback.py` | Core Celery task — the AI feedback pipeline |
| `frontend/src/api/client.ts` | Axios + JWT interceptor + silent refresh |
| `frontend/src/store/authStore.ts` | Zustand auth state with persistence |
| `frontend/src/App.tsx` | React Router + ProtectedRoute |
| `frontend/src/pages/student/AssignmentPage.tsx` | The core student UI — draft → feedback loop |
| `frontend/src/pages/teacher/GradingPage.tsx` | Click-to-grade rubric interface |

---

## What Phase 1 Does NOT Cover (→ Later Phases)

| Feature | Phase |
|---|---|
| WebSocket real-time notifications | 2 |
| Deadline reminder (Celery Beat) | 2 |
| Grade trends chart | 2 |
| Submission count live update (teacher) | 2 |
| Similarity detection | 3 |
| Bulk feedback tool | 3 |
| At-risk student detection | 3 |
| PDF reports | 3 |
| Admin/HOD dashboard | 3 |
| Security hardening + full test suite | 4 |
| Production deployment | 4 |
