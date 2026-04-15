"""
Notification service — create DB records and optionally send email.
"""
import json
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.notification import Notification
from app.utils.websocket_manager import manager


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    type: str,
    title: str,
    message: str,
    data: Optional[dict] = None,
    send_ws: bool = True,
) -> Notification:
    """Creates a notification DB record and optionally pushes it via WebSocket."""
    notif = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        data=json.dumps(data) if data else None,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    if send_ws:
        await manager.send_personal_message(
            {
                "type": type,
                "title": title,
                "message": message,
                **(data or {}),
            },
            str(user_id),
        )

    return notif


def send_email_sync(to_email: str, subject: str, html_body: str) -> None:
    """Synchronous email sender — safe to call from Celery workers."""
    if not settings.EMAIL_ENABLED or not settings.SMTP_HOST:
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls(context=context)
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
    except Exception:
        pass  # Email is best-effort — never crash the app


def grade_released_email(student_name: str, assignment_title: str, score: int, total: int) -> str:
    return f"""
    <div style="font-family:Inter,sans-serif;background:#09090B;color:#fff;padding:32px;border-radius:12px;max-width:480px">
      <h2 style="margin:0 0 8px;font-size:18px">📊 Grade Released</h2>
      <p style="color:#a1a1aa;margin:0 0 16px">Hi {student_name}, your grade for <strong>{assignment_title}</strong> is ready.</p>
      <div style="background:#1a1a1e;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:16px;text-align:center">
        <span style="font-size:36px;font-weight:700;color:#7c3aed">{score}</span>
        <span style="font-size:20px;color:#52525b">/{total}</span>
      </div>
      <p style="color:#52525b;font-size:12px;margin-top:16px">Log in to ClassPulse to view detailed feedback.</p>
    </div>
    """


def new_assignment_email(student_name: str, assignment_title: str, classroom_name: str, deadline: str) -> str:
    return f"""
    <div style="font-family:Inter,sans-serif;background:#09090B;color:#fff;padding:32px;border-radius:12px;max-width:480px">
      <h2 style="margin:0 0 8px;font-size:18px">📝 New Assignment</h2>
      <p style="color:#a1a1aa;margin:0 0 16px">Hi {student_name}, a new assignment has been posted in <strong>{classroom_name}</strong>.</p>
      <div style="background:#1a1a1e;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:16px">
        <p style="margin:0;font-weight:600">{assignment_title}</p>
        <p style="margin:4px 0 0;color:#a1a1aa;font-size:13px">Due: {deadline}</p>
      </div>
    </div>
    """
