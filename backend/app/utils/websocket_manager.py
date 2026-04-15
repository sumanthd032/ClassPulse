"""
In-process WebSocket connection manager.

Maps user_id → active WebSocket so that any part of the API can push a
JSON message to a specific connected user.

Note on scaling: this in-memory store only works when a single API process
handles all connections.  For a multi-worker deployment, replace with a
Redis pub/sub fanout (subscribe per user, publish from workers).
"""
import logging
from typing import Dict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Tracks all active WebSocket connections, keyed by user_id (str)."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept the handshake and register the connection."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info("WebSocket connected: user=%s  total=%d", user_id, len(self.active_connections))

    def disconnect(self, user_id: str) -> None:
        """Remove a user's connection when they disconnect."""
        self.active_connections.pop(user_id, None)
        logger.info("WebSocket disconnected: user=%s  total=%d", user_id, len(self.active_connections))

    async def send_personal_message(self, message: dict, user_id: str) -> None:
        """
        Push a JSON message to a specific user.
        Silently no-ops if the user is not currently connected (e.g. they
        closed their browser before the async task completed).
        """
        websocket = self.active_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as exc:
                logger.warning("Failed to send WS message to user=%s: %s", user_id, exc)
                self.disconnect(user_id)

    async def broadcast(self, message: dict) -> None:
        """Push a message to every connected user (use sparingly)."""
        for user_id, ws in list(self.active_connections.items()):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(user_id)


# Single global instance shared across the entire process
manager = ConnectionManager()
