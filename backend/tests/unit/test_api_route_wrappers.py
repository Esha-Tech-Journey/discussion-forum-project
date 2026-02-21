from types import SimpleNamespace

from app.api.v1 import auth, comments, likes, mentions, moderation, notifications, search, threads, users
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RefreshTokenRequest
from app.schemas.comment import CommentCreate, CommentUpdate
from app.schemas.like import LikeCreate
from app.schemas.moderation import ModerationCreate, ModerationUpdate, ReportCreate
from app.schemas.thread import ThreadCreate, ThreadUpdate
from app.schemas.user import UserRoleUpdate, UserUpdate


def _user(user_id: int = 1):
    return SimpleNamespace(id=user_id)


def test_auth_routes_delegate(monkeypatch):
    monkeypatch.setattr("app.api.v1.auth.AuthService.register_user", lambda *_a, **_k: {"id": 1})
    monkeypatch.setattr("app.api.v1.auth.AuthService.login_user", lambda *_a, **_k: {"access_token": "a", "refresh_token": "r", "token_type": "bearer"})
    monkeypatch.setattr("app.api.v1.auth.AuthService.refresh_access_token", lambda *_a, **_k: "new-access")
    monkeypatch.setattr("app.api.v1.auth.AuthService.change_password", lambda *_a, **_k: {"message": "ok"})
    monkeypatch.setattr("app.api.v1.auth.UserService.update_profile", lambda *_a, **_k: {"id": 1})

    assert auth.register_user(payload=SimpleNamespace(), db=None)["id"] == 1
    assert auth.login_user(payload=LoginRequest(email="a@b.com", password="pw"), db=None)["token_type"] == "bearer"
    assert auth.refresh_token(payload=RefreshTokenRequest(refresh_token="x"), db=None)["access_token"] == "new-access"
    assert auth.change_password(payload=ChangePasswordRequest(email="a@b.com", old_password="pw", new_password="newpw"), db=None)["message"] == "ok"
    assert auth.get_current_user_profile(current_user=_user(7)).id == 7
    assert auth.update_current_user_profile(payload=UserUpdate(name="x"), db=None, current_user=_user(1))["id"] == 1


def test_thread_comment_like_search_routes_delegate(monkeypatch):
    monkeypatch.setattr("app.api.v1.threads.ThreadService.create_thread", lambda *_a, **_k: {"id": 1})
    monkeypatch.setattr("app.api.v1.threads.ThreadService.list_threads", lambda *_a, **_k: {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1})
    monkeypatch.setattr("app.api.v1.threads.ThreadService.get_thread", lambda *_a, **_k: {"id": 1})
    monkeypatch.setattr("app.api.v1.threads.ThreadService.update_thread", lambda *_a, **_k: {"id": 1, "title": "u"})
    monkeypatch.setattr("app.api.v1.threads.ThreadService.delete_thread", lambda *_a, **_k: None)

    monkeypatch.setattr("app.api.v1.comments.CommentService.create_comment", lambda *_a, **_k: {"id": 1})
    monkeypatch.setattr("app.api.v1.comments.CommentService.list_thread_comments", lambda *_a, **_k: [{"id": 1}])
    monkeypatch.setattr("app.api.v1.comments.CommentService.update_comment", lambda *_a, **_k: {"id": 1})
    monkeypatch.setattr("app.api.v1.comments.CommentService.delete_comment", lambda *_a, **_k: None)

    monkeypatch.setattr("app.api.v1.likes.LikeService.add_like", lambda *_a, **_k: {"id": 1})
    monkeypatch.setattr("app.api.v1.likes.LikeService.remove_like", lambda *_a, **_k: None)
    monkeypatch.setattr("app.api.v1.search.SearchService.search_threads", lambda *_a, **_k: {"results": [], "total": 0})
    monkeypatch.setattr("app.api.v1.search.SearchService.search_comments", lambda *_a, **_k: {"results": [], "total": 0})
    monkeypatch.setattr("app.api.v1.mentions.MentionService.get_user_mentions", lambda *_a, **_k: {"items": [], "total": 0, "page": 1, "size": 20})

    actor = _user(1)
    assert threads.create_thread(ThreadCreate(title="t", description="d"), db=None, user=actor)["id"] == 1
    assert threads.list_threads(page=1, size=20, db=None, user=actor)["total"] == 0
    assert threads.get_thread(1, db=None, user=actor)["id"] == 1
    assert threads.update_thread(1, ThreadUpdate(title="x"), db=None, user=actor)["title"] == "u"
    assert threads.delete_thread(1, db=None, user=actor)["message"] == "Thread deleted"

    assert comments.create_comment(CommentCreate(content="c", thread_id=1), db=None, user=actor)["id"] == 1
    assert comments.list_comments(1, db=None, user=actor)[0]["id"] == 1
    assert comments.update_comment(1, CommentUpdate(content="x"), db=None, user=actor)["id"] == 1
    assert comments.delete_comment(1, db=None, user=actor)["message"] == "Comment deleted"

    assert likes.add_like(LikeCreate(thread_id=1, comment_id=None), db=None, user=actor)["id"] == 1
    assert likes.remove_like(LikeCreate(thread_id=1, comment_id=None), db=None, user=actor)["message"] == "Like removed"
    assert search.search_threads(q="hello", db=None)["total"] == 0
    assert search.search_comments(q="hello", db=None)["total"] == 0
    assert mentions.list_mentions(db=None, user=actor)["total"] == 0


def test_notification_moderation_user_routes_delegate(monkeypatch):
    monkeypatch.setattr("app.api.v1.notifications.NotificationService.get_user_notifications", lambda *_a, **_k: {"items": [], "total": 0, "page": 1, "size": 20})
    monkeypatch.setattr("app.api.v1.notifications.NotificationService.mark_as_read", lambda *_a, **_k: {"id": 1, "is_read": True})
    monkeypatch.setattr("app.api.v1.notifications.NotificationService.mark_all_as_read", lambda *_a, **_k: 3)
    monkeypatch.setattr("app.api.v1.notifications.NotificationService.get_unread_count", lambda *_a, **_k: 9)

    monkeypatch.setattr("app.api.v1.moderation.ModerationService.create_review", lambda *_a, **_k: {"id": 1})
    monkeypatch.setattr("app.api.v1.moderation.ModerationService.list_pending_reviews", lambda *_a, **_k: [{"id": 1}])
    monkeypatch.setattr("app.api.v1.moderation.ModerationService.list_completed_reviews", lambda *_a, **_k: [{"id": 2}])
    monkeypatch.setattr("app.api.v1.moderation.ModerationService.update_review", lambda *_a, **_k: {"id": 1, "status": "COMPLETED"})

    monkeypatch.setattr("app.api.v1.users.UserService.get_profile", lambda *_a, **_k: {"id": 1})
    monkeypatch.setattr("app.api.v1.users.UserService.suggest_users", lambda *_a, **_k: [{"id": 2}])
    monkeypatch.setattr("app.api.v1.users.UserService.get_user_activity", lambda *_a, **_k: {"stats": {}})
    monkeypatch.setattr("app.api.v1.users.UserService.list_users", lambda *_a, **_k: {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1})
    monkeypatch.setattr("app.api.v1.users.UserService.list_users_by_role_with_stats", lambda *_a, **_k: {"items": [], "total": 0, "page": 1, "size": 20, "pages": 1})
    monkeypatch.setattr("app.api.v1.users.UserService.update_user", lambda *_a, **_k: {"id": 1})
    monkeypatch.setattr("app.api.v1.users.UserService.set_user_role", lambda *_a, **_k: {"id": 1})

    actor = _user(1)
    assert notifications.get_notifications(page=1, size=20, db=None, user=actor)["total"] == 0
    assert notifications.mark_notification_read(1, db=None, user=actor)["is_read"] is True
    assert notifications.mark_all_notifications_read(db=None, user=actor)["updated"] == 3
    assert notifications.get_unread_count(db=None, user=actor)["unread_count"] == 9

    assert moderation.create_review(ModerationCreate(content_type="THREAD", thread_id=1), db=None, _=actor)["id"] == 1
    assert moderation.report_content(ReportCreate(content_type="THREAD", thread_id=1, reason="spam"), db=None, _=actor)["id"] == 1
    assert moderation.get_pending_reviews(db=None, _=actor)[0]["id"] == 1
    assert moderation.get_completed_reviews(db=None, _=actor)[0]["id"] == 2
    assert moderation.update_review(1, ModerationUpdate(status="COMPLETED"), db=None, user=actor)["status"] == "COMPLETED"
    assert moderation.take_action_on_review(1, ModerationUpdate(status="COMPLETED"), db=None, user=actor)["status"] == "COMPLETED"

    assert users.get_profile(db=None, user=actor)["id"] == 1
    assert users.suggest_users(q="a", limit=8, db=None, user=actor)[0]["id"] == 2
    assert users.get_user_activity(1, db=None, admin=actor)["stats"] == {}
    assert users.list_users(db=None, _=actor)["total"] == 0
    assert users.list_users_by_role_with_stats(role_name="MEMBER", db=None, _=actor)["total"] == 0
    assert users.update_user(1, UserUpdate(name="x"), db=None, admin=actor)["id"] == 1
    assert users.set_user_role(1, UserRoleUpdate(role_name="MODERATOR"), db=None, admin=actor)["id"] == 1
