import ast
import json
import logging

from fastapi import WebSocket
from typing import Dict, List, Set

from app.integrations.redis_client import (
    redis_client
)
from app.core.constants import RedisChannels


class ConnectionManager:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        self.connection_to_user: Dict[WebSocket, int] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int
    ):
        await websocket.accept()
        self.active_connections.append(websocket)

        self.connection_to_user[websocket] = user_id
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        user_id = self.connection_to_user.pop(websocket, None)

        if user_id is not None and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                self.user_connections.pop(user_id, None)

    async def send_personal_message(
        self,
        message: dict,
        websocket: WebSocket
    ):
        await websocket.send_json(message)

    async def send_user_message(
        self,
        user_id: int,
        message: dict
    ):
        sockets = list(self.user_connections.get(user_id, set()))
        for websocket in sockets:
            try:
                await websocket.send_json(message)
            except Exception:
                self.logger.warning(
                    "Failed to send websocket message to user_id=%s; disconnecting socket",
                    user_id,
                    exc_info=True,
                )
                self.disconnect(websocket)

    async def send_notification_to_user(
        self,
        user_id: int,
        payload: dict,
    ):
        await self.send_user_message(user_id, payload)

    def is_user_online(self, user_id: int) -> bool:
        return bool(self.user_connections.get(user_id))

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

    @staticmethod
    def _decode_redis_payload(data):
        if isinstance(data, dict):
            return data

        if not isinstance(data, str):
            return {"redis_event": data}

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(data)
            except (SyntaxError, ValueError):
                return {"redis_event": data}

    # ==============================
    # Redis Subscriber Listener
    # ==============================
    async def listen_to_channel(self, channel: str):

        pubsub = await redis_client.subscribe(channel)

        async for msg in pubsub.listen():
            if msg["type"] == "message":
                payload = self._decode_redis_payload(msg["data"])

                if (
                    channel == RedisChannels.NOTIFICATIONS
                    and isinstance(payload, dict)
                ):
                    user_id = (
                        payload.get("data", {})
                        .get("user_id")
                    )
                    if user_id is not None:
                        await self.send_notification_to_user(
                            int(user_id),
                            payload
                        )
                        continue

                if isinstance(payload, dict):
                    await self.broadcast(payload)
                else:
                    await self.broadcast({
                        "redis_event": payload
                    })


manager = ConnectionManager()
