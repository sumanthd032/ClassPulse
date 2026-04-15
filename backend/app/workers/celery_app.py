"""
Celery application configuration.

Workers:
  - ai_feedback  : generate rubric-aligned LLM feedback for each draft
  - similarity   : plagiarism check after a final submission
  - cron_tasks   : nightly late-penalty sweep
  - reminders    : daily "due tomorrow" notifications
  - at_risk      : weekly at-risk student sweep

Celery Beat runs the scheduled tasks.  Start it with:
  celery -A app.workers.celery_app beat --loglevel=info
"""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "classpulse",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.ai_feedback",
        "app.workers.auto_grade",
        "app.workers.similarity",
        "app.workers.cron_tasks",
        "app.workers.reminders",
        "app.workers.at_risk",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Retry policy for transient failures
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ---------------------------------------------------------------------------
# Scheduled tasks (Celery Beat)
# ---------------------------------------------------------------------------
celery_app.conf.beat_schedule = {
    # Apply late penalties every night at midnight UTC
    "apply-late-penalties-midnight": {
        "task": "app.workers.cron_tasks.apply_late_penalties",
        "schedule": crontab(hour=0, minute=0),
    },
    # Send "due tomorrow" reminders every morning at 8:00 UTC
    "send-due-tomorrow-reminders-8am": {
        "task": "app.workers.reminders.send_due_tomorrow_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    # At-risk student sweep every Sunday at 9:00 UTC
    "sweep-at-risk-students-weekly": {
        "task": "app.workers.at_risk.sweep_at_risk_students",
        "schedule": crontab(hour=9, minute=0, day_of_week=0),  # 0 = Sunday
    },
}
