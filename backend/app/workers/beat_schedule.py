from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "send-deadline-reminders-hourly": {
        "task": "app.workers.tasks.notifications.send_deadline_reminders",
        "schedule": crontab(minute=0),           # every hour
    },
    "detect-at-risk-students-daily": {
        "task": "app.workers.tasks.analytics.detect_at_risk_students",
        "schedule": crontab(hour=6, minute=0),   # 6am IST daily
    },
    "cleanup-stale-notifications-weekly": {
        "task": "app.workers.tasks.notifications.cleanup_stale_notifications",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2am
    },
}
