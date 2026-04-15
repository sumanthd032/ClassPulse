"""
Notification routes.

GET    /notifications/            — list all my notifications (newest first)
PATCH  /notifications/{id}/read   — mark one notification as read
PATCH  /notifications/read-all    — mark all as read
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationResponse], summary="List my notifications")
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all notifications for the authenticated user, newest first."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)   # Safety cap — frontend should paginate for large histories
    )
    return result.scalars().all()


@router.patch("/{notification_id}/read", summary="Mark one notification as read")
async def mark_as_read(
    notification_id: str,  # keep as str to handle both UUID formats
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sets `is_read=True` for the given notification (must belong to the caller)."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalars().first()

    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.is_read = True
    await db.commit()
    return {"status": "ok"}


@router.patch("/read-all", summary="Mark all notifications as read")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk-marks every unread notification for the caller as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    unread = result.scalars().all()

    for notif in unread:
        notif.is_read = True

    await db.commit()
    return {"status": "ok", "marked": len(unread)}
