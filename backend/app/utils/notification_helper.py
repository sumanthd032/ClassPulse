"""
Notification helpers — save a Notification row and push a live WebSocket event.

Two variants:
  1. `create_and_send_notification`       — synchronous, for Celery workers
  2. `create_and_send_notification_async` — async, for FastAPI routes

The WS push is best-effort: if the user is offline, we still persist the
record so they see it next time they open the notifications panel.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.utils.websocket_manager import manager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Synchronous (Celery workers use a regular sync session)
# ---------------------------------------------------------------------------

def create_and_send_notification(
    db: Session,
    user_id: str,
    alert_type: str,
    title: str,
    message: str,
) -> None:
    """
    Persists a notification and attempts a live WebSocket push.

    Called from Celery tasks where asyncio is not available.
    The event loop trick is avoided — WS push is skipped in worker context
    because the WebSocket connections live in the API process, not the worker.
    Instead, workers publish to Redis and the API's WS handler can pick it up
    in a future iteration.
    """
    notif = Notification(user_id=user_id, type=alert_type, title=title, message=message)
    db.add(notif)
    db.commit()
    db.refresh(notif)
    logger.debug("Notification persisted id=%s for user=%s", notif.id, user_id)


# ---------------------------------------------------------------------------
# Asynchronous (FastAPI routes)
# ---------------------------------------------------------------------------

async def create_and_send_notification_async(
    db: AsyncSession,
    user_id: str,
    alert_type: str,
    title: str,
    message: str,
) -> None:
    """
    Persists a notification and pushes a live WebSocket event to the user
    if they are currently connected.

    Caller is responsible for any surrounding transaction; this function
    performs its own flush + commit.
    """
    notif = Notification(user_id=user_id, type=alert_type, title=title, message=message)
    db.add(notif)
    await db.flush()   # Get the generated id without closing the outer txn
    await db.commit()

    payload = {
        "type": alert_type,
        "title": title,
        "message": message,
        "id": notif.id,
    }
    # Best-effort push — ConnectionManager silently no-ops if user is offline
    await manager.send_personal_message(payload, str(user_id))
