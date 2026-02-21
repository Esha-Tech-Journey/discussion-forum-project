import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.exceptions import AppException, app_exception_handler
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    is_token_type,
    verify_password,
)
from app.db import session as db_session
from app.dependencies import auth as auth_dep
from app.dependencies.permissions import require_admin, require_moderator
from app.dependencies.rate_limit import comment_rate_limiter, login_rate_limiter
from app.integrations.redis_client import redis_client
from app.schemas.mention import MentionResponse
from app.utils.pagination import paginate
from app.utils.rate_limiter import RateLimiter


def _make_user(user_id: int = 1, role_names: list[str] | None = None, active: bool = True):
    roles = [SimpleNamespace(role_name=name) for name in (role_names or [])]
    return SimpleNamespace(id=user_id, roles=roles, is_active=active)


def test_security_password_and_tokens_roundtrip():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong", hashed) is False

    access = create_access_token({"sub": "1"})
    refresh = create_refresh_token({"sub": "1"})
    access_payload = decode_token(access)
    refresh_payload = decode_token(refresh)

    assert access_payload["sub"] == "1"
    assert is_token_type(access_payload, "access") is True
    assert is_token_type(refresh_payload, "refresh") is True
    assert is_token_type(None, "access") is False
    assert decode_token("invalid.token.value") is None


@pytest.mark.asyncio
async def test_app_exception_handler_returns_json_response():
    response = await app_exception_handler(
        request=SimpleNamespace(),
        exc=AppException(status_code=418, message="teapot"),
    )
    assert response.status_code == 418
    assert b"teapot" in response.body


def test_permissions_require_admin_and_moderator():
    admin = _make_user(role_names=["ADMIN"])
    moderator = _make_user(role_names=["MODERATOR"])
    member = _make_user(role_names=["MEMBER"])

    assert require_admin(admin) == admin
    assert require_moderator(admin) == admin
    assert require_moderator(moderator) == moderator

    with pytest.raises(HTTPException) as exc_admin:
        require_admin(member)
    assert exc_admin.value.status_code == 403

    with pytest.raises(HTTPException) as exc_mod:
        require_moderator(member)
    assert exc_mod.value.status_code == 403


def test_get_current_user_dependency_branches(monkeypatch):
    credentials = SimpleNamespace(credentials="token")

    class FakeQuery:
        def __init__(self, user):
            self.user = user

        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return self.user

    class FakeDB:
        def __init__(self, user):
            self.user = user

        def query(self, *_args, **_kwargs):
            return FakeQuery(self.user)

    monkeypatch.setattr(auth_dep, "decode_token", lambda _token: None)
    with pytest.raises(HTTPException) as invalid_token:
        auth_dep.get_current_user(credentials=credentials, db=FakeDB(user=None))
    assert invalid_token.value.status_code == 401

    monkeypatch.setattr(auth_dep, "decode_token", lambda _token: {"sub": "1"})
    monkeypatch.setattr(auth_dep, "is_token_type", lambda *_args, **_kwargs: False)
    with pytest.raises(HTTPException) as wrong_type:
        auth_dep.get_current_user(credentials=credentials, db=FakeDB(user=None))
    assert wrong_type.value.status_code == 401

    monkeypatch.setattr(auth_dep, "is_token_type", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(auth_dep, "decode_token", lambda _token: {})
    with pytest.raises(HTTPException) as missing_sub:
        auth_dep.get_current_user(credentials=credentials, db=FakeDB(user=None))
    assert missing_sub.value.status_code == 401

    monkeypatch.setattr(auth_dep, "decode_token", lambda _token: {"sub": "2"})
    with pytest.raises(HTTPException) as no_user:
        auth_dep.get_current_user(credentials=credentials, db=FakeDB(user=None))
    assert no_user.value.status_code == 401

    inactive_user = _make_user(user_id=2, active=False)
    with pytest.raises(HTTPException) as inactive:
        auth_dep.get_current_user(credentials=credentials, db=FakeDB(user=inactive_user))
    assert inactive.value.status_code == 403

    active_user = _make_user(user_id=2, active=True)
    resolved_user = auth_dep.get_current_user(credentials=credentials, db=FakeDB(user=active_user))
    assert resolved_user.id == 2


def test_get_db_dependency_closes_session(monkeypatch):
    state = {"closed": False}

    class FakeSession:
        def close(self):
            state["closed"] = True

    monkeypatch.setattr(db_session, "SessionLocal", lambda: FakeSession())
    generator = db_session.get_db()
    _ = next(generator)
    with pytest.raises(StopIteration):
        next(generator)
    assert state["closed"] is True


@pytest.mark.asyncio
async def test_dependency_rate_limiters_use_request_ip(monkeypatch):
    calls = []

    class FakeLimiter:
        def __init__(self, key_prefix: str, limit: int, window_seconds: int):
            self.key_prefix = key_prefix
            self.limit = limit
            self.window_seconds = window_seconds

        async def check_limit(self, identifier: str):
            calls.append((self.key_prefix, identifier))

    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.99"))
    monkeypatch.setattr("app.dependencies.rate_limit.RateLimiter", FakeLimiter)

    await login_rate_limiter(request)
    await comment_rate_limiter(request)

    assert ("login", "127.0.0.99") in calls
    assert ("comment", "127.0.0.99") in calls


@pytest.mark.asyncio
async def test_rate_limiter_executes_pipeline_and_fails_open(monkeypatch):
    class FakePipeline:
        def __init__(self):
            self.commands = []

        def incr(self, key: str, value: int):
            self.commands.append(("incr", key, value))

        def expire(self, key: str, window: int):
            self.commands.append(("expire", key, window))

        async def execute(self):
            return True

    class FakeRedis:
        def __init__(self):
            self._pipe = FakePipeline()

        async def get(self, _key):
            return "0"

        def pipeline(self):
            return self._pipe

    fake_redis = FakeRedis()
    monkeypatch.setattr(redis_client, "redis", fake_redis)

    limiter = RateLimiter("login", 5, 60)
    await limiter.check_limit("ip-1")
    assert ("incr", "login:ip-1", 1) in fake_redis._pipe.commands

    class BrokenRedis:
        async def get(self, _key):
            raise RuntimeError("redis unavailable")

    monkeypatch.setattr(redis_client, "redis", BrokenRedis())
    await limiter.check_limit("ip-2")


@pytest.mark.asyncio
async def test_redis_client_publish_and_subscribe():
    called = {"published": None, "subscribed": None}

    class FakePubSub:
        async def subscribe(self, channel: str):
            called["subscribed"] = channel

    class FakeRedis:
        async def publish(self, channel: str, message: str):
            called["published"] = (channel, message)

        def pubsub(self):
            return FakePubSub()

    original = redis_client.redis
    redis_client.redis = FakeRedis()
    try:
        await redis_client.publish("chan", {"ok": True})
        pubsub = await redis_client.subscribe("chan")
        assert called["subscribed"] == "chan"
        assert called["published"][0] == "chan"
        assert isinstance(pubsub, FakePubSub)
    finally:
        redis_client.redis = original


def test_paginate_mention_schema_and_email_service(capsys):
    class FakeQuery:
        def count(self):
            return 5

        def offset(self, _value):
            return self

        def limit(self, _value):
            return self

        def all(self):
            return [1, 2]

    page = paginate(FakeQuery(), page=2, limit=2)
    assert page["total"] == 5
    assert page["pages"] == 3

    mention = MentionResponse(
        id=1,
        mentioned_user_id=1,
        thread_id=2,
        comment_id=None,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    assert mention.mentioned_user_id == 1
