"""Celery task: generate_ai_feedback.

This task is the core of ClassPulse's innovation.

Why Celery (async task queue) instead of calling the LLM directly in the HTTP request?
  - LLM calls can take 5-30 seconds. An HTTP request should respond in <500ms.
  - If we called the LLM synchronously, the student would stare at a loading spinner for 30s.
  - With Celery: the API responds immediately ("draft submitted, generating feedback..."),
    and the worker processes the LLM call in the background.
  - When feedback is ready, the worker publishes a Redis pub/sub event.
  - Phase 2 WebSocket handler picks up the event and pushes it to the student's browser.

Flow:
  Student submits draft
    → FastAPI: create Submission row, enqueue generate_ai_feedback.delay(submission_id)
    → FastAPI: return 201 immediately
    → [background] Celery worker: picks up task from Redis queue
    → [background] Worker: fetches submission + rubric from DB
    → [background] Worker: calls LLM API
    → [background] Worker: stores AIFeedback rows in DB
    → [background] Worker: publishes Redis event "feedback_ready"
    → [Phase 2] WebSocket handler: receives Redis event, pushes to student's browser
"""

import asyncio
import uuid
import json

from celery import shared_task
from sqlalchemy import select

from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="app.workers.tasks.ai_feedback.generate_ai_feedback",
    max_retries=3,
    default_retry_delay=10,     # retry after 10s if LLM API is down
)
def generate_ai_feedback(self, submission_id: str):
    """
    Celery task — runs in the worker process (not the API process).
    `bind=True` gives us access to `self` so we can call self.retry().
    Celery tasks are synchronous by default, but our DB calls are async.
    We use asyncio.run() to run the async work inside the sync Celery task.
    """
    asyncio.run(_async_generate_feedback(self, submission_id))


async def _async_generate_feedback(task, submission_id: str):
    """The actual async implementation — called via asyncio.run() from the Celery task."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    import redis.asyncio as aioredis

    from app.config import settings
    from app.models.submission import Submission
    from app.models.assignment import RubricCriterion
    from app.models.ai_feedback import AIFeedback
    from app.services.llm_service import generate_feedback

    # Create a fresh DB engine for this worker process.
    # We don't share the main app's engine — Celery workers are separate processes.
    engine = create_async_engine(settings.database_url, pool_size=5)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with SessionLocal() as db:
            # 1. Fetch the submission
            sub_result = await db.execute(
                select(Submission).where(Submission.id == uuid.UUID(submission_id))
            )
            submission = sub_result.scalar_one_or_none()
            if not submission:
                return  # submission deleted before task ran — silently exit

            # 2. Fetch the rubric criteria for the assignment
            criteria_result = await db.execute(
                select(RubricCriterion)
                .where(RubricCriterion.assignment_id == submission.assignment_id)
                .order_by(RubricCriterion.order_index)
            )
            criteria = criteria_result.scalars().all()
            if not criteria:
                return  # no rubric — can't generate feedback

            # 3. Build criteria dicts for the LLM service
            criteria_dicts = [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "max_marks": c.max_marks,
                    "levels": c.levels,
                }
                for c in criteria
            ]

            # 4. Call LLM (with caching + retry logic inside generate_feedback)
            try:
                feedback_items = await generate_feedback(
                    criteria=criteria_dicts,
                    submission_content=submission.content,
                    submission_id=submission_id,
                    rubric_id=str(submission.assignment_id),
                )
            except Exception as exc:
                # If LLM is down, retry the Celery task with exponential backoff
                raise task.retry(exc=exc)

            # 5. Delete any old AI feedback for this submission (idempotent — safe to retry)
            from sqlalchemy import delete
            await db.execute(
                delete(AIFeedback).where(AIFeedback.submission_id == uuid.UUID(submission_id))
            )

            # 6. Store per-criterion feedback rows
            for item in feedback_items:
                feedback_row = AIFeedback(
                    submission_id=uuid.UUID(submission_id),
                    criterion_id=uuid.UUID(item["criterion_id"]),
                    estimated_score=item["estimated_score"],
                    feedback_text=f"{item.get('strengths', '')} | To improve: {item.get('improvements', '')}",
                )
                db.add(feedback_row)

            await db.commit()

        # 7. Publish Redis event so Phase 2 WebSocket handler can push to the student
        redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.publish(
            f"user:{submission.student_id}:notifications",
            json.dumps({
                "type": "feedback_ready",
                "submission_id": submission_id,
            }),
        )
        await redis_client.aclose()

    finally:
        await engine.dispose()
