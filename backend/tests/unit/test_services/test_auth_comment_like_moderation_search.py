from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.auth import RefreshTokenRequest
from app.schemas.comment import CommentCreate, CommentUpdate
from app.schemas.like import LikeCreate
from app.schemas.moderation import ModerationCreate, ModerationUpdate
from app.schemas.thread import ThreadCreate
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.services.comment_service import CommentService
from app.services.like_service import LikeService
from app.services.moderation_service import ModerationService
from app.services.search_service import SearchService


def _user(user_id: int, role_names: list[str] | None = None, active: bool = True):
    return SimpleNamespace(
        id=user_id,
        email=f"user{user_id}@example.com",
        name=f"User {user_id}",
        password_hash="hashed::pw",
        is_active=active,
        roles=[SimpleNamespace(role_name=role) for role in (role_names or [])],
    )


def test_auth_service_register_login_change_password_and_refresh(monkeypatch):
    state = {"created": None, "updated": None}
    member_role = SimpleNamespace(role_name="MEMBER")
    active_user = _user(1, ["MEMBER"], active=True)
    inactive_user = _user(2, ["MEMBER"], active=False)

    class FakeUserRepo:
        def get_by_email(self, _db, email):
            if email == "exists@example.com":
                return active_user
            if email == "inactive@example.com":
                return inactive_user
            if email == "missing@example.com":
                return None
            if email == "login@example.com":
                return active_user
            if email == "inactive-login@example.com":
                return inactive_user
            if email == "change@example.com":
                return active_user
            return None

        def create_with_roles(self, _db, user_data, roles):
            state["created"] = (user_data, roles)
            return _user(10, ["MEMBER"], active=True)

        def update(self, _db, _user, data):
            state["updated"] = data
            return _user

        def get_by_id(self, _db, user_id):
            if user_id == 777:
                return None
            if user_id == 555:
                return inactive_user
            return active_user

    class FakeRoleRepo:
        def get_by_name(self, _db, role_name):
            return member_role if role_name == "MEMBER" else None

    monkeypatch.setattr(AuthService, "user_repo", FakeUserRepo())
    monkeypatch.setattr(AuthService, "role_repo", FakeRoleRepo())
    monkeypatch.setattr("app.services.auth_service.from_thread.run", lambda *_a, **_k: None)
    monkeypatch.setattr("app.services.auth_service.create_access_token", lambda data: f"access:{data['sub']}")
    monkeypatch.setattr("app.services.auth_service.create_refresh_token", lambda data: f"refresh:{data['sub']}")
    monkeypatch.setattr("app.services.auth_service.decode_token", lambda token: {"sub": token.split(":")[-1], "typ": "refresh"})
    monkeypatch.setattr("app.services.auth_service.is_token_type", lambda payload, expected: payload and payload.get("typ") == expected)
    monkeypatch.setattr("app.services.auth_service.hash_password", lambda password: f"hashed::{password}")
    monkeypatch.setattr("app.services.auth_service.verify_password", lambda plain, hashed: hashed == f"hashed::{plain}")

    with pytest.raises(HTTPException):
        AuthService.register_user(None, UserCreate(email="exists@example.com", password="pw"))

    created = AuthService.register_user(None, UserCreate(email="new@example.com", password="pw"))
    assert created.id == 10
    assert state["created"][0]["email"] == "new@example.com"

    tokens = AuthService.login_user(None, "login@example.com", "pw")
    assert tokens["access_token"] == "access:1"
    assert tokens["refresh_token"] == "refresh:1"

    with pytest.raises(HTTPException):
        AuthService.login_user(None, "missing@example.com", "pw")
    with pytest.raises(HTTPException):
        AuthService.login_user(None, "login@example.com", "wrong")
    with pytest.raises(HTTPException):
        AuthService.login_user(None, "inactive-login@example.com", "pw")

    with pytest.raises(HTTPException):
        AuthService.change_password(None, "missing@example.com", "pw", "newpw")
    with pytest.raises(HTTPException):
        AuthService.change_password(None, "inactive@example.com", "pw", "newpw")
    with pytest.raises(HTTPException):
        AuthService.change_password(None, "change@example.com", "bad", "newpw")
    with pytest.raises(HTTPException):
        AuthService.change_password(None, "change@example.com", "pw", "pw")
    with pytest.raises(HTTPException):
        AuthService.change_password(None, "change@example.com", "pw", "123")

    msg = AuthService.change_password(None, "change@example.com", "pw", "newpass")
    assert msg["message"] == "Password updated successfully"
    assert state["updated"]["password_hash"] == "hashed::newpass"

    with pytest.raises(ValueError):
        AuthService.refresh_access_token(None, "invalid")
    monkeypatch.setattr("app.services.auth_service.decode_token", lambda _token: {"typ": "refresh"})
    with pytest.raises(HTTPException):
        AuthService.refresh_access_token(None, "refresh:missing")
    monkeypatch.setattr("app.services.auth_service.decode_token", lambda _token: {"sub": "777", "typ": "refresh"})
    with pytest.raises(HTTPException):
        AuthService.refresh_access_token(None, "refresh:777")
    monkeypatch.setattr("app.services.auth_service.decode_token", lambda _token: {"sub": "555", "typ": "refresh"})
    with pytest.raises(HTTPException):
        AuthService.refresh_access_token(None, "refresh:555")
    monkeypatch.setattr("app.services.auth_service.decode_token", lambda _token: {"sub": "1", "typ": "refresh"})
    assert AuthService.refresh_access_token(None, "refresh:1") == "access:1"


def test_comment_service_branches(monkeypatch):
    thread = SimpleNamespace(id=9, is_deleted=False, author_id=2)
    parent = SimpleNamespace(id=5, is_deleted=False, thread_id=9, author_id=3)
    created_comment = SimpleNamespace(
        id=11,
        created_at="x",
        updated_at="x",
        content="hello @alice",
        thread_id=9,
        author_id=1,
        author=SimpleNamespace(id=1, name="Actor", email="actor@example.com", avatar_url=None),
        parent_comment_id=5,
        likes=[],
        is_deleted=False,
    )
    mutable = {"comment": created_comment}

    class Repo:
        def get_by_id(self, _db, comment_id):
            if comment_id == 5:
                return parent
            return mutable["comment"] if mutable["comment"] and mutable["comment"].id == comment_id else None

        def create(self, _db, data):
            mutable["comment"].thread_id = data["thread_id"]
            mutable["comment"].author_id = data["author_id"]
            mutable["comment"].parent_comment_id = data.get("parent_comment_id")
            return mutable["comment"]

        def get_thread_comments(self, _db, _thread_id, page=1, size=100):
            return [mutable["comment"]]

        def update(self, _db, comment, payload):
            comment.content = payload["content"]
            return comment

        def soft_delete(self, _db, comment):
            comment.is_deleted = True

    monkeypatch.setattr(CommentService, "repo", Repo())
    monkeypatch.setattr(CommentService, "thread_repo", SimpleNamespace(get_by_id=lambda *_a, **_k: thread))
    monkeypatch.setattr(CommentService, "user_repo", SimpleNamespace(get_by_id=lambda *_a, **_k: _user(1, ["MEMBER"])))
    monkeypatch.setattr("app.services.comment_service.ModerationService.create_review", lambda *_a, **_k: None)
    monkeypatch.setattr("app.services.comment_service.MentionService.process_mentions", lambda *_a, **_k: [_user(1), _user(4)])
    monkeypatch.setattr("app.services.comment_service.NotificationService.create_notification", lambda *_a, **_k: None)
    monkeypatch.setattr("app.services.comment_service.from_thread.run", lambda *_a, **_k: None)

    monkeypatch.setattr(CommentService, "thread_repo", SimpleNamespace(get_by_id=lambda *_a, **_k: None))
    with pytest.raises(HTTPException):
        CommentService.create_comment(None, CommentCreate(content="x", thread_id=77), 1)
    monkeypatch.setattr(CommentService, "thread_repo", SimpleNamespace(get_by_id=lambda *_a, **_k: thread))

    bad_parent = SimpleNamespace(id=7, is_deleted=False, thread_id=99, author_id=3)
    monkeypatch.setattr(CommentService, "repo", SimpleNamespace(
        get_by_id=lambda *_a, **_k: bad_parent,
        create=lambda *_a, **_k: created_comment,
    ))
    with pytest.raises(HTTPException):
        CommentService.create_comment(None, CommentCreate(content="x", thread_id=9, parent_comment_id=7), 1)

    repo = Repo()
    monkeypatch.setattr(CommentService, "repo", repo)
    created = CommentService.create_comment(
        None,
        CommentCreate(content="hello @alice", thread_id=9, parent_comment_id=5),
        1,
    )
    assert created["id"] == 11

    listed = CommentService.list_thread_comments(None, 9, 1)
    assert listed[0]["id"] == 11

    updated = CommentService.update_comment(None, 11, CommentUpdate(content="edited"), 1, _user(1, ["MEMBER"]))
    assert updated["content"] == "edited"

    with pytest.raises(HTTPException):
        CommentService.update_comment(None, 11, CommentUpdate(content="no"), 2, _user(2, ["MEMBER"]))
    with pytest.raises(HTTPException):
        CommentService.delete_comment(None, 11, 2, _user(2, ["MEMBER"]))

    CommentService.delete_comment(None, 11, 1, _user(1, ["MEMBER"]))
    assert created_comment.is_deleted is True

    mutable["comment"] = None
    with pytest.raises(HTTPException):
        CommentService.update_comment(None, 99, CommentUpdate(content="x"), 1, _user(1, ["MEMBER"]))
    with pytest.raises(HTTPException):
        CommentService.delete_comment(None, 99, 1, _user(1, ["MEMBER"]))


def test_like_moderation_and_search_services(monkeypatch):
    like = SimpleNamespace(id=1, thread_id=3, comment_id=None)
    thread = SimpleNamespace(id=3, author_id=2)
    comment = SimpleNamespace(id=4, author_id=2)
    review = SimpleNamespace(id=22, status="PENDING")

    class LikeRepo:
        def __init__(self):
            self.existing = None
            self.removed = False

        def get_user_like(self, *_a, **_k):
            return self.existing

        def create(self, _db, _data):
            self.existing = like
            return like

        def count_thread_likes(self, *_a, **_k):
            return 10

        def count_comment_likes(self, *_a, **_k):
            return 7

        def remove_like(self, _db, _like):
            self.removed = True
            self.existing = None

    like_repo = LikeRepo()
    monkeypatch.setattr(LikeService, "repo", like_repo)
    monkeypatch.setattr(LikeService, "thread_repo", SimpleNamespace(get_by_id=lambda *_a, **_k: thread))
    monkeypatch.setattr(LikeService, "comment_repo", SimpleNamespace(get_by_id=lambda *_a, **_k: comment))
    monkeypatch.setattr(LikeService, "user_repo", SimpleNamespace(get_by_id=lambda *_a, **_k: _user(1)))
    monkeypatch.setattr("app.services.like_service.NotificationService.create_notification", lambda *_a, **_k: None)
    monkeypatch.setattr("app.services.like_service.from_thread.run", lambda *_a, **_k: None)

    with pytest.raises(HTTPException):
        LikeService.add_like(None, LikeCreate(thread_id=None, comment_id=None), 1)

    created_like = LikeService.add_like(None, LikeCreate(thread_id=3, comment_id=None), 1)
    assert created_like.id == 1
    with pytest.raises(HTTPException):
        LikeService.add_like(None, LikeCreate(thread_id=3, comment_id=None), 1)

    LikeService.remove_like(None, LikeCreate(thread_id=3, comment_id=None), 1)
    assert like_repo.removed is True
    with pytest.raises(HTTPException):
        LikeService.remove_like(None, LikeCreate(thread_id=3, comment_id=None), 1)

    class ModRepo:
        def create(self, _db, _data):
            return review

        def get_pending_reviews(self, _db):
            return [review]

        def get_completed_reviews(self, _db):
            return [review]

        def get_by_id(self, _db, review_id):
            return review if review_id == 22 else None

        def update(self, _db, _review, data):
            review.status = data["status"]
            return review

    monkeypatch.setattr(ModerationService, "repo", ModRepo())
    monkeypatch.setattr("app.services.moderation_service.from_thread.run", lambda *_a, **_k: None)

    created_review = ModerationService.create_review(None, ModerationCreate(content_type="THREAD", thread_id=3))
    assert created_review.id == 22
    assert ModerationService.list_pending_reviews(None)[0].id == 22
    assert ModerationService.list_completed_reviews(None)[0].id == 22
    updated_review = ModerationService.update_review(None, 22, ModerationUpdate(status="COMPLETED"), reviewer_id=1)
    assert updated_review.status == "COMPLETED"
    with pytest.raises(HTTPException):
        ModerationService.update_review(None, 999, ModerationUpdate(status="COMPLETED"), reviewer_id=1)

    monkeypatch.setattr(SearchService, "repo", SimpleNamespace(search_threads=lambda *_a, **_k: [SimpleNamespace(id=1)]))
    assert SearchService.search_threads(None, "") == {"results": [], "total": 0}
    assert SearchService.search_threads(None, "abc")["total"] == 1
