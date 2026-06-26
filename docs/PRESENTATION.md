# ClassPulse — Presentation Content

> **Instructions for the AI model:** Generate a clean, professional **10-slide** presentation (PowerPoint / Google Slides) from the content below. Each `## Slide N` section is one slide. Use the **Title** as the slide heading and the **Bullets** as slide body text. Keep text concise — convert long sentences into short bullets. Apply the **Design Guidelines** at the bottom. Where a slide says *[Visual]*, add the suggested diagram, icon set, or screenshot placeholder.

---

## Slide 1 — Title

**Title:** ClassPulse
**Subtitle:** AI-Powered Classroom Management for Engineering Colleges

**Bullets:**
- Students submit drafts and get instant LLM feedback before the deadline
- Teachers grade faster with AI-suggested scores and real-time plagiarism flags

**Presented by (Group Members):**
- Sumantha — USN: 1BM23IS260
- Shrijani Bhat — USN: 1BM23IS242
- Samarth P — USN: 1BM23IS214

**Submitted to:** Rashmi P, Assistant Professor, Department of Information Science & Engineering (ISE), BMS College of Engineering (BMSCE)

*[Visual: Large project logo, violet + teal accent theme, clean hero layout; place group members and "Submitted to" details neatly at the bottom]*

---

## Slide 2 — Problem Statement

**Title:** The Problem

**Bullets:**
- Students receive feedback only **after** the deadline — too late to improve
- Manual grading is slow, inconsistent, and time-consuming for teachers
- Plagiarism between submissions is hard to detect at scale
- No single platform connects drafting, feedback, grading, and analytics
- HODs/Admins lack visibility into at-risk students and class performance

*[Visual: Icons for "late feedback", "manual grading", "plagiarism"; before/after contrast]*

---

## Slide 3 — Proposed Solution

**Title:** Our Solution

**Bullets:**
- A **draft → instant AI feedback loop** so students improve before the deadline
- **Rubric-aligned AI grading** that suggests scores per criterion to teachers
- **Automatic plagiarism detection** with real-time teacher alerts
- **Role-based dashboards** for Students, Teachers, and Admins/HODs
- One integrated platform: submit, feedback, grade, notify, analyze

*[Visual: Central "ClassPulse" hub connecting the three user roles]*

---

## Slide 4 — Key Features

**Title:** Key Features

**Bullets:**
- **Draft → Feedback Loop** — submit up to N drafts; each triggers instant AI feedback aligned to the rubric
- **Rubric-Aligned AI Grading** — Google Gemini scores each criterion (excellent / good / average / poor) with estimated marks
- **TF-IDF Plagiarism Detection** — flags submission pairs above 80% cosine similarity
- **Real-Time Notifications** — WebSocket push for grades, new assignments, plagiarism flags, deadlines
- **Role-Based Access** — Student, Teacher, Admin/HOD dashboards and permissions
- **Automated Background Jobs** — late penalties, deadline reminders, at-risk student detection

*[Visual: 6 feature cards with icons in a 2x3 grid]*

---

## Slide 5 — System Architecture

**Title:** System Architecture

**Bullets:**
- **Frontend:** React SPA (Vite, Tailwind, Zustand, React Query) over HTTP `/api` + WebSocket `/ws`
- **Backend:** FastAPI (uvicorn) — Auth, Classrooms, Assignments, Submissions, Grading, Notifications, Dashboard, Admin
- **Data:** PostgreSQL 16 (all persistent data) via async SQLAlchemy
- **Cache / Broker:** Redis 7 — tokens, rate-limits, pub/sub, Celery broker
- **Workers:** Celery — AI feedback, similarity checks, late penalties, reminders

*[Visual: Layered architecture diagram — Browser → FastAPI → PostgreSQL + Redis → Celery Workers. Recreate the box diagram from the README.]*

---

## Slide 6 — Technology Stack

**Title:** Technology Stack

**Bullets:**
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Zustand, React Query, Framer Motion, Recharts
- **Backend:** FastAPI 0.111, Python 3.11, SQLAlchemy 2.0 (async), Pydantic
- **Database:** PostgreSQL 16 (asyncpg + psycopg2)
- **Cache / Queue:** Redis 7, Celery (+ Celery Beat)
- **AI / ML:** Google Gemini API, scikit-learn (TF-IDF), NumPy
- **Auth:** JWT (python-jose), bcrypt
- **Infra:** Docker + Docker Compose, MinIO (object storage for file uploads)

*[Visual: Technology logos grouped by layer]*

---

## Slide 7 — How It Works (Workflow)

**Title:** How It Works

**Bullets:**
1. Teacher creates an assignment with a **rubric** and deadline
2. Student submits a **draft** → Celery runs **AI feedback** against the rubric
3. Student revises and submits the **final** version
4. System runs **TF-IDF plagiarism check** + **AI-suggested grading**
5. Teacher reviews AI suggestions, finalizes grades, releases them
6. Student gets a **real-time notification**; Admin sees class analytics

*[Visual: Horizontal numbered flow / user-journey arrows]*

---

## Slide 8 — Screenshots / Demo

**Title:** Live Demo

**Bullets:**
- **Student Dashboard** — assignments, draft feedback, grades
- **Teacher Dashboard** — grading view with AI suggestions + plagiarism flags
- **Admin / HOD Dashboard** — class analytics and at-risk students
- Real-time notification panel and submission timeline

*[Visual: 3 app screenshot placeholders — Student, Teacher, Admin views. Insert real screenshots here.]*

---

## Slide 9 — Results & Challenges

**Title:** Results & Challenges

**Bullets:**
- **Achieved:** end-to-end draft-feedback loop, AI grading, plagiarism detection, real-time notifications, 3 role-based dashboards
- **Automation:** Celery Beat handles late penalties (midnight UTC), reminders (8am), weekly at-risk detection
- **Challenges solved:**
  - Async AI grading without blocking the API (Celery + Redis)
  - Reliable real-time push via WebSockets + Redis pub/sub
  - Tuning plagiarism similarity threshold for accuracy
- **Learnings:** prompt design for rubric-aligned grading, scalable async architecture

*[Visual: Checklist of completed items + a small challenges/solutions table]*

---

## Slide 10 — Future Scope & Conclusion

**Title:** Future Scope & Conclusion

**Bullets:**
- **Future scope:**
  - Support multiple LLM providers and model comparison
  - Mobile app for students
  - Deeper analytics and learning-outcome tracking
  - Semantic (embedding-based) plagiarism detection
- **Conclusion:** ClassPulse closes the feedback gap — faster grading for teachers, earlier guidance for students, and clear visibility for administrators
- **Thank You — Questions?**

*[Visual: Roadmap arrow + closing thank-you banner]*

---

## Design Guidelines (for the AI generating the deck)

- **Slide count:** exactly 10.
- **Theme:** modern, minimal, professional. Accent colors: **violet (#7C3AED)** and **teal (#009688)**; light background; dark readable text.
- **Typography:** sans-serif (e.g., Inter, Poppins, or Calibri); large headings, generous spacing.
- **Text density:** max ~6 bullets per slide, short phrases not paragraphs.
- **Visuals:** add icons, diagrams, and the architecture/workflow graphics described in each *[Visual]* note; leave clearly labeled placeholders for screenshots.
- **Consistency:** same header style, footer with slide number + "ClassPulse" on every slide.
- **Tone:** confident and technical but accessible to a general academic audience.
