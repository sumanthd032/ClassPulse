"""
Cron task: "Due tomorrow" reminders.

Scheduled: Every morning at 08:00 UTC (via Celery Beat).
Sends a REMINDER notification to every student enrolled in a classroom that
has an assignment with a deadline in the next 24 hours.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.assignment import Assignment
from app.models.classroom import Enrollment, EnrollmentRole
from app.models.notification import Notification
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_SYNC_DB_URL = settings.DATABASE_URL.replace("+asyncpg", "")
_engine = create_engine(_SYNC_DB_URL, pool_pre_ping=True)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@celery_app.task
def send_due_tomorrow_reminders() -> str:
    """
    Finds all published assignments with a deadline in the next 24 hours and
    sends a REMINDER notification to every enrolled student.

    Returns a summary string for the Celery result backend.
    """
    logger.info("Due-tomorrow reminder sweep started")
    db = _SessionLocal()

    try:
        now = datetime.now(timezone.utc)
        window_start = now
        window_end = now + timedelta(hours=24)

        # Find all published assignments due within the next 24 hours
        upcoming = (
            db.query(Assignment)
            .filter(
                Assignment.is_published == True,         # noqa: E712
                Assignment.deadline >= window_start,
                Assignment.deadline <= window_end,
            )
            .all()
        )

        count = 0
        for assignment in upcoming:
            students = (
                db.query(Enrollment)
                .filter(
                    Enrollment.classroom_id == assignment.classroom_id,
                    Enrollment.role == EnrollmentRole.student,
                )
                .all()
            )

            for enrollment in students:
                db.add(
                    Notification(
                        user_id=str(enrollment.user_id),
                        type="REMINDER",
                        title="Assignment Due Tomorrow!",
                        message=(
                            f"'{assignment.title}' is due in less than 24 hours. "
                            "Make sure your final submission is ready!"
                        ),
                    )
                )
                count += 1

        if count:
            db.commit()
            logger.info("Sent %d reminder notifications", count)
        else:
            logger.info("No assignments due tomorrow — no reminders sent")

        return f"sent:{count}"

    except Exception as exc:
        db.rollback()
        logger.exception("Reminder sweep failed")
        raise exc
    finally:
        db.close()
