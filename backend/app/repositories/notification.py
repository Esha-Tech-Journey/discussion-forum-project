from sqlalchemy.orm import Session
from sqlalchemy import func, select, update, and_
from datetime import datetime, timedelta, timezone

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):

    def __init__(self):
        super().__init__(Notification)

    # ==============================
    # Get user notifications
    # ==============================
    def get_user_notifications(
        self,
        db: Session,
        user_id: int,
        page: int = 1,
        size: int = 20,
    ):
        offset = (page - 1) * size

        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(size)
        )

        return list(db.scalars(stmt).all())

    def count_user_notifications(
        self,
        db: Session,
        user_id: int,
    ) -> int:
        stmt = (
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id)
        )
        return int(db.scalar(stmt) or 0)

    def get_unread_count(
        self,
        db: Session,
        user_id: int,
    ) -> int:
        stmt = (
            select(func.count(Notification.id))
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return int(db.scalar(stmt) or 0)

    def get_user_notification_by_id(
        self,
        db: Session,
        user_id: int,
        notification_id: int,
    ) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        return db.scalar(stmt)

    def mark_all_as_read(
        self,
        db: Session,
        user_id: int,
    ) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        result = db.execute(stmt)
        db.commit()
        return int(result.rowcount or 0)

    def mark_as_read(
        self,
        db: Session,
        notification: Notification
    ) -> Notification:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        return notification

    def find_recent_duplicate(
        self,
        db: Session,
        user_id: int,
        actor_id: int | None,
        type: str,
        entity_type: str,
        entity_id: int,
        window_seconds: int = 30,
    ) -> Notification | None:
        # Idempotency guard: if the same event is raised multiple times quickly,
        # reuse the latest unread notification instead of inserting duplicates.
        since = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        stmt = (
            select(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.type == type,
                    Notification.entity_type == entity_type,
                    Notification.entity_id == entity_id,
                    Notification.is_read.is_(False),
                    Notification.created_at >= since,
                    (
                        Notification.actor_id == actor_id
                        if actor_id is not None
                        else Notification.actor_id.is_(None)
                    ),
                )
            )
            .order_by(Notification.created_at.desc())
            .limit(1)
        )
        return db.scalar(stmt)
