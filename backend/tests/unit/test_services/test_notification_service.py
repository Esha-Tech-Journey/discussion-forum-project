from app.services.notification_service import NotificationService
from app.repositories.user import UserRepository


def _create_user(db, email: str):
    repo = UserRepository()
    return repo.create(
        db,
        {
            "email": email,
            "password_hash": "hashed",
        },
    )


def test_create_notification_persists_for_offline_user(db, monkeypatch):
    user = _create_user(db, "offline-notify@test.com")

    monkeypatch.setattr(
        "app.services.notification_service.manager.is_user_online",
        lambda user_id: False,
    )

    notification = NotificationService.create_notification(
        db=db,
        user_id=user.id,
        actor_id=None,
        type="SYSTEM",
        title="Test",
        message="Offline notification",
        entity_type="thread",
        entity_id=1,
    )

    assert notification.id is not None
    assert notification.user_id == user.id
    assert notification.is_read is False


def test_create_notification_triggers_realtime_for_online_user(db, monkeypatch):
    user = _create_user(db, "online-notify@test.com")
    called = {"dispatched": False}

    monkeypatch.setattr(
        "app.services.notification_service.manager.is_user_online",
        lambda user_id: True,
    )

    def fake_from_thread_run(fn, *args, **kwargs):
        called["dispatched"] = fn.__name__ == "dispatch_notification_event"
        return None

    monkeypatch.setattr(
        "app.services.notification_service.from_thread.run",
        fake_from_thread_run,
    )

    NotificationService.create_notification(
        db=db,
        user_id=user.id,
        actor_id=None,
        type="SYSTEM",
        title="Realtime",
        message="Online notification",
        entity_type="thread",
        entity_id=1,
    )

    assert called["dispatched"] is True


def test_mark_all_as_read_updates_all_rows(db, monkeypatch):
    user = _create_user(db, "mark-all@test.com")
    monkeypatch.setattr(
        "app.services.notification_service.manager.is_user_online",
        lambda user_id: False,
    )

    NotificationService.create_notification(
        db=db,
        user_id=user.id,
        actor_id=None,
        type="SYSTEM",
        title="One",
        message="One",
        entity_type="thread",
        entity_id=1,
    )
    NotificationService.create_notification(
        db=db,
        user_id=user.id,
        actor_id=None,
        type="SYSTEM",
        title="Two",
        message="Two",
        entity_type="thread",
        entity_id=2,
    )

    updated = NotificationService.mark_all_as_read(
        db,
        user.id,
    )

    assert updated == 2
    assert NotificationService.get_unread_count(db, user.id) == 0
