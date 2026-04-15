"""
Cron task: Late penalty sweep.

Scheduled: Every night at midnight UTC (via Celery Beat).
Logic: Any released grade linked to a late final submission gets a 10% penalty
applied exactly once (guarded by a sentinel comment in teacher_comments).
"""
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.grade import Grade
from app.models.submission import Submission
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_SYNC_DB_URL = settings.DATABASE_URL.replace("+asyncpg", "")
_engine = create_engine(_SYNC_DB_URL, pool_pre_ping=True)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

# Sentinel string written into teacher_comments to prevent double-penalizing
_PENALTY_MARKER = "[AUTO: LATE PENALTY APPLIED]"


@celery_app.task
def apply_late_penalties() -> str:
    """
    Sweeps all released grades for late final submissions and applies a 10%
    point deduction if not already penalized.

    The penalty amount is appended to `teacher_comments` so students understand
    why their score is lower than the teacher's initial mark.

    Returns a summary string for the Celery result backend.
    """
    logger.info("Late penalty sweep started")
    db = _SessionLocal()

    try:
        # Grades for late final submissions that haven't been penalized yet
        late_grades = (
            db.query(Grade)
            .join(Submission, Submission.id == Grade.submission_id)
            .filter(
                Submission.is_late == True,      # noqa: E712
                Submission.is_final == True,     # noqa: E712
                Grade.is_released == True,       # noqa: E712 — only penalize released grades
            )
            .all()
        )

        count = 0
        for grade in late_grades:
            # Idempotency guard — skip if already penalized
            if grade.teacher_comments and _PENALTY_MARKER in grade.teacher_comments:
                continue

            penalty = max(1, int(grade.total_score * 0.10))  # At least 1 point
            grade.total_score = max(0, grade.total_score - penalty)
            grade.teacher_comments = (
                (grade.teacher_comments or "")
                + f"\n\n{_PENALTY_MARKER} (-{penalty} pts for late submission)"
            )
            count += 1

        if count:
            db.commit()
            logger.info("Late penalty applied to %d grades", count)
        else:
            logger.info("No new late penalties to apply")

        return f"penalized:{count}"

    except Exception as exc:
        db.rollback()
        logger.exception("Late penalty sweep failed")
        raise exc
    finally:
        db.close()
