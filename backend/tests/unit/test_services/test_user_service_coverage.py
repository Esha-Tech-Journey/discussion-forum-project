from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.constants import Roles
from app.models.role import Role
from app.repositories.comment import CommentRepository
from app.repositories.like import LikeRepository
from app.repositories.role import RoleRepository
from app.repositories.thread import ThreadRepository
from app.repositories.user import UserRepository
from app.services.user_service import UserService


def _ensure_roles(db):
    for role_name in (Roles.ADMIN, Roles.MODERATOR, Roles.MEMBER):
        if db.query(Role).filter(Role.role_name == role_name).first() is None:
            db.add(Role(role_name=role_name))
    db.commit()


def _create_user(db, email: str, name: str, role_name: str):
    role_repo = RoleRepository()
    role = role_repo.get_by_name(db, role_name)
    return UserRepository().create_with_roles(
        db,
        {
            "email": email,
            "password_hash": "hashed",
            "name": name,
            "is_active": True,
        },
        [role] if role else [],
    )


def test_user_service_error_paths_and_admin_promotion_notification(db, monkeypatch):
    _ensure_roles(db)
    admin = _create_user(db, "admin-us@example.com", "Admin", Roles.ADMIN)
    member = _create_user(db, "member-us@example.com", "Member", Roles.MEMBER)
    member_for_forbidden_check = _create_user(
        db,
        "member-forbidden@example.com",
        "Member Forbidden",
        Roles.MEMBER,
    )

    with pytest.raises(HTTPException) as bad_role:
        UserService.list_users_by_role_with_stats(db, role_name="UNKNOWN")
    assert bad_role.value.status_code == 400

    with pytest.raises(HTTPException) as not_admin:
        UserService.update_user(
            db,
            actor=member,
            user_id=admin.id,
            data={"name": "X"},
        )
    assert not_admin.value.status_code == 403

    with pytest.raises(HTTPException) as missing_user:
        UserService.update_user(
            db,
            actor=admin,
            user_id=99999,
            data={"name": "X"},
        )
    assert missing_user.value.status_code == 404

    with pytest.raises(HTTPException) as set_role_not_admin:
        UserService.set_user_role(
            db,
            actor=member,
            user_id=member.id,
            role_name=Roles.MODERATOR,
        )
    assert set_role_not_admin.value.status_code == 403

    with pytest.raises(HTTPException) as set_role_missing_user:
        UserService.set_user_role(
            db,
            actor=admin,
            user_id=99999,
            role_name=Roles.MODERATOR,
        )
    assert set_role_missing_user.value.status_code == 404

    with pytest.raises(HTTPException) as set_role_missing_role:
        UserService.set_user_role(
            db,
            actor=admin,
            user_id=member.id,
            role_name="NO_SUCH_ROLE",
        )
    assert set_role_missing_role.value.status_code == 400

    notifications = []
    monkeypatch.setattr(
        "app.services.user_service.NotificationService.create_notification",
        lambda *_args, **kwargs: notifications.append(kwargs),
    )
    monkeypatch.setattr(
        "app.services.user_service.from_thread.run",
        lambda *_args, **_kwargs: None,
    )

    promoted = UserService.set_user_role(
        db,
        actor=admin,
        user_id=member.id,
        role_name=Roles.ADMIN,
    )
    assert any(role.role_name == Roles.ADMIN for role in promoted.roles)
    assert any(payload["type"] == "ROLE_PROMOTION" for payload in notifications)

    with pytest.raises(HTTPException) as activity_missing:
        UserService.get_user_activity(db, actor=admin, target_user_id=99999)
    assert activity_missing.value.status_code == 404

    with pytest.raises(HTTPException) as activity_not_admin:
        UserService.get_user_activity(
            db,
            actor=member_for_forbidden_check,
            target_user_id=member.id,
        )
    assert activity_not_admin.value.status_code == 403


def test_user_service_activity_includes_truncated_comment_like_excerpt(db):
    _ensure_roles(db)
    admin = _create_user(db, "admin-activity@example.com", "Admin", Roles.ADMIN)
    target = _create_user(db, "target-activity@example.com", "Target", Roles.MEMBER)
    other = _create_user(db, "other-activity@example.com", "Other", Roles.MEMBER)

    thread_repo = ThreadRepository()
    comment_repo = CommentRepository()
    like_repo = LikeRepository()

    target_thread = thread_repo.create(
        db,
        {"title": "Target thread", "description": "description", "author_id": target.id},
    )
    other_thread = thread_repo.create(
        db,
        {"title": "Other thread", "description": "description", "author_id": other.id},
    )

    long_comment = "x" * 180
    comment = comment_repo.create(
        db,
        {"content": long_comment, "thread_id": other_thread.id, "author_id": other.id},
    )

    like_repo.create(db, {"user_id": target.id, "thread_id": other_thread.id})
    like_repo.create(db, {"user_id": target.id, "comment_id": comment.id})
    like_repo.create(db, {"user_id": other.id, "thread_id": target_thread.id})

    result = UserService.get_user_activity(
        db,
        actor=admin,
        target_user_id=target.id,
        limit_threads=10,
        limit_comments=10,
        limit_likes=10,
    )

    assert result["stats"]["threads"] >= 1
    assert result["stats"]["likes_received"] >= 1
    comment_likes = [entry for entry in result["recent_likes"] if entry["target_type"] == "comment"]
    assert len(comment_likes) == 1
    assert comment_likes[0]["comment_excerpt"].endswith("...")
    assert len(comment_likes[0]["comment_excerpt"]) == 120


def test_user_service_profile_and_suggest_delegate(db):
    _ensure_roles(db)
    member = _create_user(db, "profile-service@example.com", "Profile", Roles.MEMBER)

    profile = UserService.get_profile(db, member.id)
    assert profile.id == member.id

    updated = UserService.update_profile(db, member.id, {"bio": "Hello"})
    assert updated.bio == "Hello"

    suggestions = UserService.suggest_users(
        db,
        q="Pro",
        limit=5,
        exclude_user_id=None,
    )
    assert len(suggestions) >= 1


def test_user_service_list_and_update_success_paths(db, monkeypatch):
    _ensure_roles(db)
    admin = _create_user(db, "admin-list@example.com", "Admin List", Roles.ADMIN)
    target = _create_user(db, "target-list@example.com", "Target List", Roles.MEMBER)

    listed = UserService.list_users(db, page=1, size=10, q="list")
    assert listed["total"] >= 2
    assert listed["page"] == 1

    member_view = UserService.list_users_by_role_with_stats(
        db,
        role_name=Roles.MEMBER,
        page=1,
        size=10,
        q="list",
    )
    assert member_view["page"] == 1
    assert member_view["pages"] >= 1

    monkeypatch.setattr(
        "app.services.user_service.from_thread.run",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("ws down")),
    )
    updated = UserService.update_user(
        db,
        actor=admin,
        user_id=target.id,
        data={"name": "Target Updated"},
    )
    assert updated.name == "Target Updated"


def test_user_service_moderator_promotion_notification(db, monkeypatch):
    _ensure_roles(db)
    admin = _create_user(db, "admin-mod@example.com", "Admin Mod", Roles.ADMIN)
    member = _create_user(db, "member-mod@example.com", "Member Mod", Roles.MEMBER)

    sent = []
    monkeypatch.setattr(
        "app.services.user_service.NotificationService.create_notification",
        lambda *_a, **kwargs: sent.append(kwargs),
    )
    monkeypatch.setattr(
        "app.services.user_service.from_thread.run",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("ws down")),
    )

    promoted = UserService.set_user_role(
        db,
        actor=admin,
        user_id=member.id,
        role_name=Roles.MODERATOR,
    )
    assert any(role.role_name == Roles.MODERATOR for role in promoted.roles)
    assert any(payload["title"].endswith("Moderator") for payload in sent)
