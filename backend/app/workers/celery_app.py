from celery import Celery
from app.config import settings

celery_app = Celery(
    "classpulse",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks.ai_feedback",
        "app.workers.tasks.notifications",
        "app.workers.tasks.similarity",
        "app.workers.tasks.analytics",
        "app.workers.tasks.reports",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
)
