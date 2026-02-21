from sqlalchemy.orm import Session
from fastapi import HTTPException
from anyio import from_thread

from app.schemas.like import LikeCreate
from app.repositories.like import LikeRepository
from app.repositories.thread import ThreadRepository
from app.repositories.comment import CommentRepository
from app.repositories.user import UserRepository
from app.websocket.handlers import broadcast_new_like
from app.services.thread_service import ThreadService
from app.services.notification_service import NotificationService


class LikeService:

    repo = LikeRepository()
    thread_repo = ThreadRepository()
    comment_repo = CommentRepository()
    user_repo = UserRepository()

    # ==============================
    # Add Like
    # ==============================
    @classmethod
    def add_like(
        cls,
        db: Session,
        payload: LikeCreate,
        user_id: int
    ):

        if not payload.thread_id and not payload.comment_id:
            raise HTTPException(
                400,
                "Target ID required"
            )

        existing = cls.repo.get_user_like(
            db,
            user_id,
            payload.thread_id,
            payload.comment_id
        )

        if existing:
            raise HTTPException(
                400,
                "Already liked"
            )

        data = payload.model_dump()
        data["user_id"] = user_id

        like = cls.repo.create(db, data)

        recipient_id = None
        entity_type = None
        entity_id = None
        actor = cls.user_repo.get_by_id(db, user_id)
        actor_label = (
            actor.name
            or actor.email
            or f"User {user_id}"
        ) if actor else f"User {user_id}"
        notification_title = "New like on your content"
        notification_message = f"{actor_label} liked your content."

        if payload.thread_id:
            thread = cls.thread_repo.get_by_id(db, payload.thread_id)
            if thread:
                recipient_id = thread.author_id
                entity_type = "thread"
                entity_id = thread.id
                notification_title = "New like on your thread"
                notification_message = f"{actor_label} liked your thread."
        elif payload.comment_id:
            comment = cls.comment_repo.get_by_id(db, payload.comment_id)
            if comment:
                recipient_id = comment.author_id
                entity_type = "comment"
                entity_id = comment.id
                notification_title = "New like on your comment"
                notification_message = f"{actor_label} liked your comment."

        if (
            recipient_id is not None
            and recipient_id != user_id
            and entity_type is not None
            and entity_id is not None
        ):
            NotificationService.create_notification(
                db,
                user_id=recipient_id,
                actor_id=user_id,
                type="LIKE",
                title=notification_title,
                message=notification_message,
                entity_type=entity_type,
                entity_id=entity_id,
            )

        like_count = None
        if payload.thread_id:
            like_count = cls.repo.count_thread_likes(
                db,
                payload.thread_id
            )
            try:
                ThreadService._invalidate_threads_cache()
            except Exception:
                pass
        elif payload.comment_id:
            like_count = cls.repo.count_comment_likes(
                db,
                payload.comment_id
            )

        try:
            from_thread.run(
                broadcast_new_like,
                payload.thread_id,
                payload.comment_id,
                like_count,
                "created",
            )
        except Exception:
            # Realtime delivery failure should not rollback persisted like.
            pass

        return like

    # ==============================
    # Remove Like
    # ==============================
    @classmethod
    def remove_like(
        cls,
        db: Session,
        payload: LikeCreate,
        user_id: int
    ):

        like = cls.repo.get_user_like(
            db,
            user_id,
            payload.thread_id,
            payload.comment_id
        )

        if not like:
            raise HTTPException(404, "Like not found")

        thread_id = like.thread_id
        comment_id = like.comment_id
        cls.repo.remove_like(db, like)

        like_count = None
        if thread_id:
            like_count = cls.repo.count_thread_likes(
                db,
                thread_id
            )
            try:
                ThreadService._invalidate_threads_cache()
            except Exception:
                pass
        elif comment_id:
            like_count = cls.repo.count_comment_likes(
                db,
                comment_id
            )

        try:
            from_thread.run(
                broadcast_new_like,
                thread_id,
                comment_id,
                like_count,
                "removed",
            )
        except Exception:
            # Realtime delivery failure should not rollback persisted unlike.
            pass
