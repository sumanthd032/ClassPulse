"""
Cron task: At-risk student sweep.

Scheduled: Every Sunday at 09:00 UTC (via Celery Beat).
Sends an AT_RISK notification to any student whose average released grade
has dropped below the at-risk threshold (default: 70%).
"""
import logging

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.grade import Grade
from app.models.notification import Notification
from app.models.submission import Submission
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_SYNC_DB_URL = settings.DATABASE_URL.replace("+asyncpg", "")
_engine = create_engine(_SYNC_DB_URL, pool_pre_ping=True)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

_AT_RISK_THRESHOLD = 70.0   # Percentage — students below this receive a warning


@celery_app.task
def sweep_at_risk_students() -> str:
    """
    Computes each student's average released grade and sends an AT_RISK
    notification to anyone below the threshold.

    Only considers released grades so students are not alarmed prematurely.

    Returns a summary string for the Celery result backend.
    """
    logger.info("At-risk student sweep started")
    db = _SessionLocal()

    try:
        # Average released grade per student
        results = (
            db.query(
                Submission.student_id,
                func.avg(Grade.total_score).label("avg_score"),
            )
            .join(Grade, Submission.id == Grade.submission_id)
            .filter(Grade.is_released == True)  # noqa: E712
            .group_by(Submission.student_id)
            .all()
        )

        count = 0
        for student_id, avg_score in results:
            if avg_score is not None and float(avg_score) < _AT_RISK_THRESHOLD:
                db.add(
                    Notification(
                        user_id=str(student_id),
                        type="AT_RISK",
                        title="Academic Performance Warning",
                        message=(
                            f"Your current average is {avg_score:.1f}%, which is below "
                            f"the passing threshold of {_AT_RISK_THRESHOLD:.0f}%. "
                            "Please speak to your teacher as soon as possible."
                        ),
                    )
                )
                count += 1

        if count:
            db.commit()
            logger.info("Sent %d at-risk alerts", count)
        else:
            logger.info("All students are in good standing — no alerts sent")

        return f"alerts:{count}"

    except Exception as exc:
        db.rollback()
        logger.exception("At-risk sweep failed")
        raise exc
    finally:
        db.close()
