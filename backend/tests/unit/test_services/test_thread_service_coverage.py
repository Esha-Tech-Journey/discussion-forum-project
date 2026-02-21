from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.thread import ThreadCreate, ThreadUpdate
from app.services.thread_service import ThreadService


def _make_user(user_id: int, roles: list[str], name: str = "", email: str = ""):
    return SimpleNamespace(
        id=user_id,
        roles=[SimpleNamespace(role_name=role) for role in roles],
        name=name,
        email=email,
        avatar_url=None,
    )


def _make_thread(author_id: int = 1, deleted: bool = False):
    author = SimpleNamespace(
        id=author_id,
        name="Author",
        email="author@example.com",
        avatar_url=None,
    )
    return SimpleNamespace(
        id=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        title="Initial",
        description="Initial description",
        tags=[SimpleNamespace(name="tag1")],
        author_id=author_id,
        author=author,
        comments=[SimpleNamespace(is_deleted=False), SimpleNamespace(is_deleted=True)],
        likes=[SimpleNamespace(user_id=2)],
        is_deleted=deleted,
    )


class _FakeThreadRepo:
    def __init__(self, thread):
        self.thread = thread
        self.updated_payload = None
        self.soft_deleted = False

    def create(self, _db, data):
        self.thread.author_id = data["author_id"]
        self.thread.title = data["title"]
        self.thread.description = data["description"]
        return self.thread

    def get_active_threads(self, _db):
        return [self.thread]

    def get_by_id(self, _db, _thread_id):
        return self.thread

    def update(self, _db, thread, payload):
        self.updated_payload = payload
        for key, value in payload.items():
            setattr(thread, key, value)
        return thread

    def soft_delete(self, _db, thread):
        self.soft_deleted = True
        thread.is_deleted = True


def test_create_thread_requires_author_id():
    with pytest.raises(HTTPException) as exc:
        ThreadService.create_thread(
            db=None,
            payload=ThreadCreate(title="T", description="D"),
            author_id=None,
            user_id=None,
        )
    assert exc.value.status_code == 400


def test_create_thread_non_moderator_triggers_moderation_and_notifications(monkeypatch):
    thread = _make_thread(author_id=1)
    repo = _FakeThreadRepo(thread)
    notifications = []
    moderation_called = {"value": False}

    monkeypatch.setattr(ThreadService, "repo", repo)
    monkeypatch.setattr(
        ThreadService,
        "user_repo",
        SimpleNamespace(get_by_id=lambda _db, _uid: _make_user(1, ["MEMBER"], email="actor@example.com")),
    )
    monkeypatch.setattr(
        "app.services.thread_service.MentionService.process_mentions",
        lambda *_args, **_kwargs: [_make_user(1, []), _make_user(2, [])],
    )
    monkeypatch.setattr(
        "app.services.thread_service.NotificationService.create_notification",
        lambda *_args, **kwargs: notifications.append(kwargs),
    )
    monkeypatch.setattr(
        "app.services.thread_service.ModerationService.create_review",
        lambda *_args, **_kwargs: moderation_called.__setitem__("value", True),
    )
    monkeypatch.setattr(
        "app.services.thread_service.from_thread.run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("ws unavailable")),
    )
    monkeypatch.setattr(ThreadService, "_invalidate_threads_cache", lambda: None)

    created = ThreadService.create_thread(
        db=None,
        payload=ThreadCreate(title="New", description="Thread"),
        author_id=1,
    )

    assert created.id == 1
    assert moderation_called["value"] is True
    assert len(notifications) == 1
    assert notifications[0]["user_id"] == 2


def test_list_threads_uses_cached_payload(monkeypatch):
    cached = '[{"id":1},{"id":2},{"id":3}]'

    def fake_run_redis_call(method, *args):
        if method.__name__ == "get":
            return cached
        return None

    monkeypatch.setattr(ThreadService, "_run_redis_call", staticmethod(fake_run_redis_call))
    monkeypatch.setattr(
        ThreadService,
        "repo",
        SimpleNamespace(get_active_threads=lambda _db: (_ for _ in ()).throw(AssertionError("should not query db"))),
    )

    result = ThreadService.list_threads(db=None, page=2, size=2, user_id=None)
    assert result["total"] == 3
    assert result["items"] == [{"id": 3}]


def test_list_threads_falls_back_to_repo_and_writes_cache(monkeypatch):
    thread = _make_thread(author_id=1)
    repo = _FakeThreadRepo(thread)
    calls = []

    def fake_run_redis_call(method, *args):
        calls.append(method.__name__)
        if method.__name__ == "get":
            raise RuntimeError("cache down")
        return None

    monkeypatch.setattr(ThreadService, "repo", repo)
    monkeypatch.setattr(ThreadService, "_run_redis_call", staticmethod(fake_run_redis_call))

    result = ThreadService.list_threads(db=None, page=1, size=20, user_id=None)
    assert result["total"] == 1
    assert result["items"][0]["title"] == "Initial"
    assert "get" in calls
    assert "setex" in calls


def test_get_update_delete_permission_and_not_found_paths(monkeypatch):
    thread = _make_thread(author_id=1)
    repo = _FakeThreadRepo(thread)
    monkeypatch.setattr(ThreadService, "repo", repo)
    monkeypatch.setattr(ThreadService, "_invalidate_threads_cache", lambda: None)
    monkeypatch.setattr("app.services.thread_service.from_thread.run", lambda *_args, **_kwargs: None)

    not_author = _make_user(2, ["MEMBER"])
    with pytest.raises(HTTPException) as cannot_edit:
        ThreadService.update_thread(
            db=None,
            thread_id=1,
            payload=ThreadUpdate(title="X"),
            user_id=2,
            actor=not_author,
        )
    assert cannot_edit.value.status_code == 403

    with pytest.raises(HTTPException) as cannot_delete:
        ThreadService.delete_thread(
            db=None,
            thread_id=1,
            user_id=2,
            actor=not_author,
        )
    assert cannot_delete.value.status_code == 403

    updated = ThreadService.update_thread(
        db=None,
        thread_id=1,
        payload=ThreadUpdate(title="Updated"),
        user_id=1,
        actor=_make_user(1, ["MEMBER"]),
    )
    assert updated["title"] == "Updated"
    assert repo.updated_payload["title"] == "Updated"

    ThreadService.delete_thread(
        db=None,
        thread_id=1,
        user_id=1,
        actor=_make_user(1, ["MEMBER"]),
    )
    assert repo.soft_deleted is True

    repo.thread = None
    with pytest.raises(HTTPException) as not_found:
        ThreadService.get_thread(db=None, thread_id=9, user_id=1)
    assert not_found.value.status_code == 404
