import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.thread import ThreadRepository
from app.repositories.comment import CommentRepository
from app.repositories.like import LikeRepository
from app.repositories.notification import NotificationRepository
from app.repositories.moderation import ModerationRepository


def _create_user(db, email: str = "repo@test.com") -> User:
    repo = UserRepository()
    return repo.create(
        db,
        {
            "email": email,
            "password_hash": "hashed",
        }
    )


def test_create_user(db):
    repo = UserRepository()

    user = repo.create(
        db,
        {
            "email": "repo@test.com",
            "password_hash": "hashed",
        }
    )

    assert user.id is not None
    assert user.email == "repo@test.com"


def test_get_user_by_email(db):
    repo = UserRepository()
    _create_user(db, "repo2@test.com")

    user = repo.get_by_email(
        db,
        "repo2@test.com"
    )

    assert user is not None
    assert user.email == "repo2@test.com"


def test_create_thread(db):
    user = _create_user(db, "thread@test.com")
    repo = ThreadRepository()

    thread = repo.create(
        db,
        {
            "title": "Repo Thread",
            "description": "Testing",
            "author_id": user.id,
        }
    )

    assert thread.id is not None
    assert thread.title == "Repo Thread"


def test_create_comment(db):
    user = _create_user(db, "comment@test.com")
    thread = ThreadRepository().create(
        db,
        {
            "title": "Comment Thread",
            "description": "Testing comments",
            "author_id": user.id,
        }
    )

    repo = CommentRepository()

    comment = repo.create(
        db,
        {
            "content": "Repo Comment",
            "thread_id": thread.id,
            "author_id": user.id,
        }
    )

    assert comment.id is not None


def test_like_thread(db):
    user = _create_user(db, "like@test.com")
    thread = ThreadRepository().create(
        db,
        {
            "title": "Like Thread",
            "description": "Testing likes",
            "author_id": user.id,
        }
    )
    repo = LikeRepository()

    like = repo.create(
        db,
        {
            "user_id": user.id,
            "thread_id": thread.id,
        }
    )

    assert like.id is not None


def test_create_notification(db):
    recipient = _create_user(db, "notify@test.com")
    repo = NotificationRepository()

    notification = repo.create(
        db,
        {
            "user_id": recipient.id,
            "actor_id": None,
            "title": "Test",
            "message": "Test Notification",
            "type": "SYSTEM",
            "entity_type": "thread",
            "entity_id": 1,
        }
    )

    assert notification.id is not None


def test_create_moderation_review(db):
    user = _create_user(db, "mod@test.com")
    thread = ThreadRepository().create(
        db,
        {
            "title": "Moderation Thread",
            "description": "Testing moderation",
            "author_id": user.id,
        }
    )
    repo = ModerationRepository()

    review = repo.create(
        db,
        {
            "content_type": "THREAD",
            "thread_id": thread.id,
            "status": "PENDING",
        }
    )

    assert review.id is not None


def test_soft_delete_thread(db):
    user = _create_user(db, "softdelete@test.com")
    repo = ThreadRepository()
    thread = repo.create(
        db,
        {
            "title": "Soft Delete Thread",
            "description": "Testing soft delete",
            "author_id": user.id,
        }
    )

    repo.update(
        db,
        thread,
        {"is_deleted": True}
    )

    assert thread.is_deleted is True


def test_unique_like(db):
    user = _create_user(db, "unique-like@test.com")
    thread = ThreadRepository().create(
        db,
        {
            "title": "Unique Like Thread",
            "description": "Testing unique like",
            "author_id": user.id,
        }
    )
    repo = LikeRepository()

    repo.create(
        db,
        {"user_id": user.id, "thread_id": thread.id}
    )

    with pytest.raises(IntegrityError):
        repo.create(
            db,
            {"user_id": user.id, "thread_id": thread.id}
        )
