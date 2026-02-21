from sqlalchemy.orm import Session
from fastapi import HTTPException
from anyio import from_thread

from app.repositories.notification import (
    NotificationRepository
)
from app.websocket.manager import manager
from app.websocket.notifications_handler import (
    dispatch_notification_event,
)
from app.integrations.redis_client import redis_client


class NotificationService:

    repo = NotificationRepository()
    _count_cache_prefix = "notifications:unread_count:"
    _list_cache_prefix = "notifications:list:"
    _cache_ttl_seconds = 300

    @classmethod
    def _count_cache_key(cls, user_id: int) -> str:
        return f"{cls._count_cache_prefix}{user_id}"

    @classmethod
    def _list_cache_key(cls, user_id: int, page: int, size: int) -> str:
        return f"{cls._list_cache_prefix}{user_id}:{page}:{size}"

    @classmethod
    def _invalidate_cache(cls, user_id: int):
        try:
            from_thread.run(
                redis_client.redis.delete,
                cls._count_cache_key(user_id),
            )
            pattern = f"{cls._list_cache_prefix}{user_id}:*"
            keys = from_thread.run(
                redis_client.redis.keys,
                pattern,
            )
            if keys:
                for key in keys:
                    from_thread.run(
                        redis_client.redis.delete,
                        key,
                    )
        except Exception:
            pass

    @staticmethod
    def _serialize_notification(notification) -> dict:
        return {
            "id": notification.id,
            "created_at": notification.created_at,
            "updated_at": notification.updated_at,
            "user_id": notification.user_id,
            "actor_id": notification.actor_id,
            "type": notification.type,
            "title": notification.title,
            "message": notification.message,
            "entity_type": notification.entity_type,
            "entity_id": notification.entity_id,
            "is_read": notification.is_read,
        }

    # ==============================
    # Create Notification
    # ==============================
    @classmethod
    def create_notification(
        cls,
        db: Session,
        user_id: int,
        actor_id: int | None,
        type: str,
        title: str,
        message: str,
        entity_type: str,
        entity_id: int,
    ):

        existing = cls.repo.find_recent_duplicate(
            db,
            user_id=user_id,
            actor_id=actor_id,
            type=type,
            entity_type=entity_type,
            entity_id=entity_id,
            window_seconds=30,
        )
        if existing is not None:
            return existing

        data = {
            "user_id": user_id,
            "actor_id": actor_id,
            "type": type,
            "title": title,
            "message": message,
            "entity_type": entity_type,
            "entity_id": entity_id,
        }

        notification = cls.repo.create(db, data)
        cls._invalidate_cache(user_id)

        if manager.is_user_online(user_id):
            from_thread.run(
                dispatch_notification_event,
                notification,
            )

        return notification

    # ==============================
    # List Notifications
    # ==============================
    @classmethod
    def get_user_notifications(
        cls,
        db: Session,
        user_id: int,
        page: int = 1,
        size: int = 20,
    ):
        cache_key = cls._list_cache_key(user_id, page, size)
        cached = None
        try:
            cached = from_thread.run(
                redis_client.redis.get,
                cache_key,
            )
        except Exception:
            pass
        if cached:
            import json

            return json.loads(cached)

        items = cls.repo.get_user_notifications(
            db,
            user_id,
            page=page,
            size=size,
        )
        serialized_items = [
            cls._serialize_notification(item)
            for item in items
        ]
        total = cls.repo.count_user_notifications(
            db,
            user_id,
        )
        response = {
            "items": serialized_items,
            "total": total,
            "page": page,
            "size": size,
        }
        try:
            import json

            from_thread.run(
                redis_client.redis.setex,
                cache_key,
                cls._cache_ttl_seconds,
                json.dumps(
                    response,
                    default=str,
                ),
            )
        except Exception:
            pass

        return response

    @classmethod
    def get_unread_count(
        cls,
        db: Session,
        user_id: int,
    ) -> int:
        cache_key = cls._count_cache_key(user_id)
        try:
            cached = from_thread.run(
                redis_client.redis.get,
                cache_key,
            )
            if cached is not None:
                return int(cached)
        except Exception:
            pass

        count = cls.repo.get_unread_count(db, user_id)
        try:
            from_thread.run(
                redis_client.redis.setex,
                cache_key,
                cls._cache_ttl_seconds,
                str(count),
            )
        except Exception:
            pass
        return count

    # ==============================
    # Mark as Read
    # ==============================
    @classmethod
    def mark_as_read(
        cls,
        db: Session,
        user_id: int,
        notification_id: int,
    ):

        notification = cls.repo.get_user_notification_by_id(
            db,
            user_id,
            notification_id,
        )
        if not notification:
            raise HTTPException(404, "Notification not found")

        notification = cls.repo.mark_as_read(
            db,
            notification,
        )
        cls._invalidate_cache(user_id)

        return notification

    @classmethod
    def mark_all_as_read(
        cls,
        db: Session,
        user_id: int,
    ) -> int:
        updated = cls.repo.mark_all_as_read(
            db,
            user_id,
        )
        cls._invalidate_cache(user_id)
        return updated
