"""
AI Feedback Celery task.

Triggered when a student submits a draft.  Calls the Gemini LLM to evaluate
the submission against each rubric criterion and stores the results in the
`ai_feedback` table.

Rate limiting:
  - Max `LLM_RATE_LIMIT_PER_HOUR` (default: 5) calls per student per hour.
  - Enforced via a Redis counter with a 1-hour sliding window.

Caching:
  - The LLM response is cached in Redis for 1 hour, keyed by a SHA-256 hash
    of (submission content + assignment id).  Identical resubmissions get
    instant feedback without an extra API call.

Retry policy:
  - On LLM failure (timeout, bad JSON), retries up to 3 times with a 30-second
    exponential backoff.
"""
import hashlib
import json
import logging
from uuid import UUID as PyUUID

import httpx
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.assignment import Assignment, RubricCriteria
from app.models.feedback import AIFeedback
from app.models.submission import Submission
from app.utils.llm_client import call_llm
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Synchronous DB + Redis — Celery workers run in a separate sync process
_SYNC_DB_URL = settings.DATABASE_URL.replace("+asyncpg", "")
_engine = create_engine(_SYNC_DB_URL, pool_pre_ping=True)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

_SYSTEM_PROMPT = (
    "You are an academic feedback assistant for an Indian engineering college. "
    "Evaluate the student's submission against each rubric criterion. "
    "For each criterion return:\n"
    "  - criterion_id (copy from input)\n"
    "  - estimated_score (integer, 0 to max_marks)\n"
    "  - strengths (what the student did well — be specific)\n"
    "  - improvements (actionable suggestions — never say 'wrong', say 'to improve, add X')\n"
    "  - suggested_level ('excellent' | 'good' | 'average' | 'poor')\n"
    "Tone: encouraging, constructive, and direct.  "
    "Output ONLY a valid JSON array — one object per criterion, no extra text."
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def generate_ai_feedback(self, submission_id: str) -> str:
    """
    Generates rubric-aligned AI feedback for a single draft submission.

    Args:
        submission_id: UUID string of the Submission row.

    Returns:
        A status string ("success", "skipped", "rate_limited").

    Raises:
        Retries on LLM errors up to max_retries times.
    """
    db = _SessionLocal()
    try:
        # ----------------------------------------------------------------
        # 1. Load data
        # ----------------------------------------------------------------
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.warning("Submission %s not found — skipping", submission_id)
            return "skipped:not_found"
        if submission.is_final:
            logger.info("Submission %s is final — AI feedback skipped", submission_id)
            return "skipped:is_final"
        if not submission.content:
            logger.info("Submission %s has no text content — skipping", submission_id)
            return "skipped:no_content"

        assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
        rubric_criteria = (
            db.query(RubricCriteria)
            .filter(RubricCriteria.assignment_id == assignment.id)
            .order_by(RubricCriteria.order_index)
            .all()
        )

        # ----------------------------------------------------------------
        # 2. Rate limit — max N calls per student per hour
        # ----------------------------------------------------------------
        rate_key = f"rate:llm:{submission.student_id}"
        call_count = _redis.incr(rate_key)
        if call_count == 1:
            _redis.expire(rate_key, 3600)  # Reset window after 1 hour
        if call_count > settings.LLM_RATE_LIMIT_PER_HOUR:
            logger.info(
                "Rate limit hit for student %s (%d calls)",
                submission.student_id,
                call_count,
            )
            return "rate_limited"

        # ----------------------------------------------------------------
        # 3. Cache check — skip LLM if content hasn't changed
        # ----------------------------------------------------------------
        content_hash = hashlib.sha256(
            f"{submission.content}|{assignment.id}".encode()
        ).hexdigest()
        cache_key = f"llm_cache:{content_hash}"
        cached = _redis.get(cache_key)

        if cached:
            evaluations = json.loads(cached)
            logger.debug("LLM cache hit for submission %s", submission_id)
        else:
            # ----------------------------------------------------------------
            # 4. Call the LLM
            # ----------------------------------------------------------------
            rubric_data = [
                {
                    "criterion_id": str(c.id),
                    "name": c.name,
                    "max_marks": c.max_marks,
                    "levels": c.levels,
                }
                for c in rubric_criteria
            ]

            user_prompt = (
                f"Assignment: {assignment.title}\n\n"
                f"Rubric:\n{json.dumps(rubric_data, indent=2)}\n\n"
                f"Student submission:\n{submission.content}\n\n"
                "Return a JSON array — one object per criterion with exactly these keys: "
                "criterion_id, estimated_score, strengths, improvements, suggested_level"
            )

            try:
                evaluations = call_llm(_SYSTEM_PROMPT, user_prompt)
                _redis.setex(cache_key, 3600, json.dumps(evaluations))
            except httpx.HTTPStatusError as exc:
                if exc.response is not None and exc.response.status_code == 429:
                    logger.warning(
                        "Gemini 429 for submission %s — retrying in 60s (attempt %d/3)",
                        submission_id, self.request.retries + 1,
                    )
                    raise self.retry(exc=exc, countdown=60)
                logger.error("LLM HTTP error for submission %s: %s", submission_id, exc)
                raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))
            except Exception as exc:
                logger.error("LLM call failed for submission %s: %s", submission_id, exc)
                raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))

        # ----------------------------------------------------------------
        # 5. Persist feedback rows (replace any previous feedback for this draft)
        # ----------------------------------------------------------------
        # Remove stale feedback so we don't accumulate duplicates on retry
        db.query(AIFeedback).filter(AIFeedback.submission_id == submission.id).delete()

        for item in evaluations:
            db.add(
                AIFeedback(
                    submission_id=submission.id,
                    criterion_id=PyUUID(item["criterion_id"]),
                    estimated_score=item["estimated_score"],
                    feedback_text=(
                        f"Strengths: {item['strengths']}\n"
                        f"Improvements: {item['improvements']}"
                    ),
                    suggested_level=item.get("suggested_level", "average"),
                )
            )
        db.commit()

        # ----------------------------------------------------------------
        # 6. Persist notification in DB (best-effort — no WS from worker)
        # ----------------------------------------------------------------
        from app.models.notification import Notification
        db.add(
            Notification(
                user_id=submission.student_id,
                type="FEEDBACK_READY",
                title="AI Feedback Ready!",
                message=f"Your feedback for '{assignment.title}' (draft {submission.draft_number}) is available.",
            )
        )
        db.commit()

        logger.info("AI feedback generated for submission %s", submission_id)
        return "success"

    except Exception as exc:
        db.rollback()
        logger.exception("generate_ai_feedback failed for %s", submission_id)
        raise exc
    finally:
        db.close()
