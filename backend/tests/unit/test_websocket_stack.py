from types import SimpleNamespace

import pytest

from app.core.constants import RedisChannels
from app.websocket import handlers
from app.websocket.events import WSEvents
from app.websocket.manager import ConnectionManager
from app.websocket.notifications_handler import (
    build_notification_payload,
    dispatch_notification_event,
)


class FakeWebSocket:
    def __init__(self):
        self.accepted = False
        self.messages = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        self.messages.append(message)


@pytest.mark.asyncio
async def test_connection_manager_core_behaviors():
    manager = ConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    await manager.connect(ws1, user_id=10)
    await manager.connect(ws2, user_id=10)
    assert ws1.accepted is True
    assert manager.is_user_online(10) is True

    await manager.send_personal_message({"ping": True}, ws1)
    await manager.send_user_message(10, {"hello": "user"})
    await manager.send_notification_to_user(10, {"event": "notif"})
    await manager.broadcast({"event": "all"})

    assert ws1.messages[0] == {"ping": True}
    assert {"hello": "user"} in ws2.messages

    manager.disconnect(ws1)
    manager.disconnect(ws2)
    assert manager.is_user_online(10) is False


@pytest.mark.asyncio
async def test_connection_manager_send_user_message_disconnects_failed_socket():
    manager = ConnectionManager()

    class BrokenWebSocket(FakeWebSocket):
        async def send_json(self, _message):
            raise RuntimeError("socket closed")

    ws = BrokenWebSocket()
    await manager.connect(ws, user_id=11)
    await manager.send_user_message(11, {"will": "fail"})
    assert manager.is_user_online(11) is False


def test_decode_redis_payload_variants():
    manager = ConnectionManager()
    assert manager._decode_redis_payload({"ok": 1}) == {"ok": 1}
    assert manager._decode_redis_payload('{"ok": 2}') == {"ok": 2}
    assert manager._decode_redis_payload("{'ok': 3}") == {"ok": 3}
    assert manager._decode_redis_payload("raw") == {"redis_event": "raw"}
    assert manager._decode_redis_payload(123) == {"redis_event": 123}


@pytest.mark.asyncio
async def test_listen_to_channel_routes_notifications_and_broadcasts(monkeypatch):
    manager = ConnectionManager()
    sent_to_user = []
    broadcasted = []

    async def fake_send_notification_to_user(user_id: int, payload: dict):
        sent_to_user.append((user_id, payload))

    async def fake_broadcast(payload: dict):
        broadcasted.append(payload)

    class FakePubSub:
        async def listen(self):
            yield {
                "type": "message",
                "data": '{"data": {"user_id": 5}, "event": "NEW_NOTIFICATION"}',
            }
            yield {
                "type": "message",
                "data": '{"event": "NEW_THREAD"}',
            }

    async def fake_subscribe(_channel: str):
        return FakePubSub()

    monkeypatch.setattr("app.websocket.manager.redis_client.subscribe", fake_subscribe)
    monkeypatch.setattr(manager, "send_notification_to_user", fake_send_notification_to_user)
    monkeypatch.setattr(manager, "broadcast", fake_broadcast)

    await manager.listen_to_channel(RedisChannels.NOTIFICATIONS)

    assert sent_to_user[0][0] == 5
    assert any(payload.get("event") == "NEW_THREAD" for payload in broadcasted)


@pytest.mark.asyncio
async def test_handlers_publish_expected_messages(monkeypatch):
    published = []
    broadcasted = []

    async def fake_publish(channel: str, message: dict):
        published.append((channel, message))

    async def fake_broadcast(message: dict):
        broadcasted.append(message)

    monkeypatch.setattr("app.websocket.handlers.redis_client.publish", fake_publish)
    monkeypatch.setattr("app.websocket.handlers.manager.broadcast", fake_broadcast)

    thread = SimpleNamespace(
        id=1,
        title="T",
    )
    user = SimpleNamespace(
        id=2,
        email="u@example.com",
        name="U",
        avatar_url=None,
        bio=None,
        is_active=True,
        created_at="2024-01-01",
        roles=[SimpleNamespace(id=1, role_name="MEMBER")],
    )
    review = SimpleNamespace(
        id=3,
        content_type="THREAD",
        thread_id=1,
        comment_id=None,
        reason=None,
        reviewer_id=2,
        status="PENDING",
        action_taken=None,
        created_at="2024-01-01",
        updated_at="2024-01-01",
    )
    comment = SimpleNamespace(id=4, thread_id=1, content="c")

    await handlers.broadcast_new_comment(comment)
    await handlers.broadcast_new_thread(thread, "updated")
    await handlers.broadcast_new_like(thread_id=1, like_count=3, action="created")
    await handlers.broadcast_new_user(user, "updated")
    await handlers.broadcast_moderation_review(review, "updated")

    events = [msg[1]["event"] for msg in published]
    assert WSEvents.NEW_COMMENT in events
    assert WSEvents.NEW_THREAD in events
    assert WSEvents.NEW_LIKE in events
    assert WSEvents.NEW_USER in events
    assert WSEvents.MODERATION_REVIEW in events
    assert len(broadcasted) == 5


@pytest.mark.asyncio
async def test_notification_payload_and_dispatch_fallback(monkeypatch):
    notification = SimpleNamespace(
        id=99,
        user_id=7,
        actor_id=1,
        type="SYSTEM",
        title="Hi",
        message="Body",
        entity_type="thread",
        entity_id=5,
        is_read=False,
        created_at="2024-01-01",
    )

    payload = build_notification_payload(notification)
    assert payload["event"] == WSEvents.NEW_NOTIFICATION
    assert payload["data"]["user_id"] == 7

    sent = []

    async def raise_publish(_channel: str, _message: dict):
        raise RuntimeError("redis down")

    async def fake_send_notification_to_user(user_id: int, data: dict):
        sent.append((user_id, data))

    monkeypatch.setattr(
        "app.websocket.notifications_handler.redis_client.publish",
        raise_publish,
    )
    monkeypatch.setattr(
        "app.websocket.notifications_handler.manager.send_notification_to_user",
        fake_send_notification_to_user,
    )

    await dispatch_notification_event(notification)
    assert sent[0][0] == 7
