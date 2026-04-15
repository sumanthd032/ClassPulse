"""
WebSocket endpoint for real-time push notifications.

Clients connect with:
  ws://host/ws?token=<JWT_ACCESS_TOKEN>

The server only pushes; clients do not send messages.
Events pushed:
  - GRADE_RELEASED       — when a teacher releases a grade
  - FEEDBACK_READY       — when AI feedback completes for a draft
  - NEW_ASSIGNMENT       — when a new assignment is posted in a classroom
  - PLAGIARISM_FLAG      — when high similarity is detected (teacher only)
  - REMINDER             — upcoming deadline reminder
  - AT_RISK              — at-risk student alert
"""
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.config import settings
from app.utils.websocket_manager import manager

router = APIRouter(tags=["WebSocket"])
logger = logging.getLogger(__name__)


def _decode_ws_token(token: str) -> str | None:
    """
    Decodes the JWT to extract the user_id (sub claim).
    Returns None if the token is invalid — the caller then rejects the connection.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token for authentication"),
):
    """
    Authenticated WebSocket connection.

    The client must pass a valid JWT as a query parameter.
    On invalid/expired tokens the connection is closed with code 1008 (Policy Violation).
    """
    user_id = _decode_ws_token(token)

    if not user_id:
        logger.warning("WebSocket rejected: invalid token")
        await websocket.close(code=1008)  # 1008 = Policy Violation
        return

    await manager.connect(websocket, user_id)

    try:
        # Keep connection open — the server only pushes; we discard any client messages
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)
