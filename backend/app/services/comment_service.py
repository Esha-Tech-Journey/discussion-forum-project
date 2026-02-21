from sqlalchemy.orm import Session
from fastapi import HTTPException
from anyio import from_thread

from app.core.constants import Roles
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
)
from app.models.user import User
from app.repositories.comment import CommentRepository
from app.repositories.thread import ThreadRepository
from app.repositories.user import UserRepository
from app.websocket.handlers import broadcast_new_comment
from app.services.moderation_service import ModerationService
from app.services.thread_service import ThreadService
from app.services.notification_service import (
    NotificationService
)
from app.services.mention_service import (
    MentionService
)
from app.schemas.moderation import ModerationCreate


class CommentService:

    repo = CommentRepository()
    thread_repo = ThreadRepository()
    user_repo = UserRepository()

    @staticmethod
    def _is_moderator_or_admin(user: User) -> bool:
        return any(
            role.role_name in {Roles.ADMIN, Roles.MODERATOR}
            for role in user.roles
        )

    @staticmethod
    def _serialize_comment(comment, user_id: int | None = None) -> dict:
        likes = list(comment.likes or [])
        return {
            "id": comment.id,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "content": comment.content,
            "thread_id": comment.thread_id,
            "author_id": comment.author_id,
            "author": (
                {
                    "id": comment.author.id,
                    "name": comment.author.name,
                    "email": comment.author.email,
                    "avatar_url": comment.author.avatar_url,
                }
                if comment.author
                else None
            ),
            "parent_comment_id": comment.parent_comment_id,
            "like_count": len(likes),
            "user_has_liked": any(
                like.user_id == user_id for like in likes
            ) if user_id is not None else False,
            "is_deleted": comment.is_deleted,
        }

    # ==============================
    # Create Comment / Reply
    # ==============================
    @classmethod
    def create_comment(
        cls,
        db: Session,
        payload: CommentCreate,
        user_id: int
    ):
        thread = cls.thread_repo.get_by_id(
            db,
            payload.thread_id,
        )
        if not thread or thread.is_deleted:
            raise HTTPException(404, "Thread not found")

        parent = None
        if payload.parent_comment_id is not None:
            parent = cls.repo.get_by_id(
                db,
                payload.parent_comment_id
            )
            if not parent or parent.is_deleted:
                raise HTTPException(
                    400,
                    "Parent comment not found"
                )
            if parent.thread_id != payload.thread_id:
                raise HTTPException(
                    400,
                    "Parent comment does not belong to thread"
                )

        data = payload.model_dump()
        data["author_id"] = user_id

        comment = cls.repo.create(db, data)

        actor = cls.user_repo.get_by_id(db, user_id)
        if actor is None or not cls._is_moderator_or_admin(actor):
            ModerationService.create_review(
                db,
                ModerationCreate(
                    content_type="COMMENT",
                    thread_id=comment.thread_id,
                    comment_id=comment.id,
                ),
            )

        mentioned_users = MentionService.process_mentions(
            db,
            payload.content,
            thread_id=comment.thread_id,
            comment_id=comment.id,
        )
        notified_user_ids: set[int] = set()

        actor_label = (
            (actor.name or "").strip()
            or actor.email
            or "Someone"
        )
        for user in mentioned_users:
            if user.id == user_id:
                continue

            NotificationService.create_notification(
                db,
                user_id=user.id,
                actor_id=user_id,
                type="MENTION",
                title="Mentioned in a comment",
                message=f"{actor_label} mentioned you in a comment.",
                entity_type="comment",
                entity_id=comment.id,
            )
            notified_user_ids.add(user.id)

        thread_author_id = thread.author_id
        if (
            thread_author_id != user_id
            and thread_author_id not in notified_user_ids
        ):
            NotificationService.create_notification(
                db,
                user_id=thread_author_id,
                actor_id=user_id,
                type="THREAD_COMMENT",
                title="New comment on your thread",
                message="Someone commented on your thread.",
                entity_type="thread",
                entity_id=comment.thread_id,
            )
            notified_user_ids.add(thread_author_id)

        if parent is not None:
            if (
                parent.author_id != user_id
                and parent.author_id not in notified_user_ids
            ):
                NotificationService.create_notification(
                    db,
                    user_id=parent.author_id,
                    actor_id=user_id,
                    type="REPLY",
                    title="New reply to your comment",
                    message="Someone replied to your comment.",
                    entity_type="comment",
                    entity_id=comment.id,
                )
        try:
            ThreadService._invalidate_threads_cache()
        except Exception:
            pass

        try:
            from_thread.run(broadcast_new_comment, comment)
        except Exception:
            # Realtime broadcast is best-effort; comment is already persisted.
            pass

        return cls._serialize_comment(comment, user_id)

    # ==============================
    # Get Thread Comments
    # ==============================
    @classmethod
    def list_thread_comments(
        cls,
        db: Session,
        thread_id: int,
        page: int = 1,
        size: int = 100,
        user_id: int | None = None,
    ):
        comments = cls.repo.get_thread_comments(
            db,
            thread_id,
            page=page,
            size=size,
        )
        return [
            cls._serialize_comment(comment, user_id)
            for comment in comments
        ]

    # ==============================
    # Update Comment
    # ==============================
    @classmethod
    def update_comment(
        cls,
        db: Session,
        comment_id: int,
        payload: CommentUpdate,
        user_id: int,
        actor: User
    ):

        comment = cls.repo.get_by_id(db, comment_id)

        if not comment or comment.is_deleted:
            raise HTTPException(404, "Comment not found")

        if (
            comment.author_id != user_id
            and not cls._is_moderator_or_admin(actor)
        ):
            raise HTTPException(403, "Not allowed")

        updated = cls.repo.update(
            db,
            comment,
            payload.model_dump()
        )
        return cls._serialize_comment(updated, user_id)

    # ==============================
    # Delete Comment
    # ==============================
    @classmethod
    def delete_comment(
        cls,
        db: Session,
        comment_id: int,
        user_id: int,
        actor: User
    ):

        comment = cls.repo.get_by_id(db, comment_id)

        if not comment or comment.is_deleted:
            raise HTTPException(404, "Comment not found")

        if (
            comment.author_id != user_id
            and not cls._is_moderator_or_admin(actor)
        ):
            raise HTTPException(403, "Not allowed")

        cls.repo.soft_delete(
            db,
            comment,
        )
        try:
            ThreadService._invalidate_threads_cache()
        except Exception:
            pass
