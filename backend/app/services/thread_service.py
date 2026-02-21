import asyncio
import math
import json

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from anyio import from_thread

from app.models.thread import Thread
from app.models.user import User
from app.core.constants import Roles
from app.schemas.thread import ThreadCreate, ThreadUpdate
from app.repositories.thread import ThreadRepository
from app.repositories.tag import TagRepository
from app.repositories.user import UserRepository
from app.repositories.like import LikeRepository
from app.models.tag import Tag
from app.integrations.redis_client import redis_client
from app.websocket.handlers import broadcast_new_thread
from app.services.mention_service import MentionService
from app.services.moderation_service import ModerationService
from app.services.notification_service import NotificationService
from app.schemas.moderation import ModerationCreate


class ThreadService:

    repo = ThreadRepository()
    user_repo = UserRepository()
    tag_repo = TagRepository()
    like_repo = LikeRepository()
    _threads_cache_key = "threads:list"
    _threads_cache_ttl_seconds = 300

    @staticmethod
    def _is_moderator_or_admin(user: User) -> bool:
        return any(
            role.role_name in {Roles.ADMIN, Roles.MODERATOR}
            for role in user.roles
        )

    @staticmethod
    def _serialize_thread(thread: Thread, user_id: int | None = None) -> dict:
        likes = list(thread.likes or [])
        comments = list(thread.comments or [])
        return {
            "id": thread.id,
            "created_at": thread.created_at,
            "updated_at": thread.updated_at,
            "title": thread.title,
            "description": thread.description,
            "tags": [tag.name for tag in thread.tags],
            "author_id": thread.author_id,
            "author": (
                {
                    "id": thread.author.id,
                    "name": thread.author.name,
                    "email": thread.author.email,
                    "avatar_url": thread.author.avatar_url,
                }
                if thread.author
                else None
            ),
            "comment_count": sum(
                1 for comment in comments
                if not comment.is_deleted
            ),
            "like_count": len(likes),
            "user_has_liked": any(
                like.user_id == user_id for like in likes
            ) if user_id is not None else False,
            "is_deleted": thread.is_deleted,
        }

    @staticmethod
    def _run_redis_call(method, *args):
        try:
            return asyncio.run(method(*args))
        except RuntimeError:
            return from_thread.run(method, *args)

    @classmethod
    def _invalidate_threads_cache(cls):
        try:
            cls._run_redis_call(
                redis_client.redis.delete,
                cls._threads_cache_key,
            )
        except Exception:
            pass

    # ==============================
    # Create Thread
    # ==============================
    @classmethod
    def create_thread(
        cls,
        db: Session,
        payload: ThreadCreate,
        author_id: int | None = None,
        user_id: int | None = None,
    ) -> Thread:

        if author_id is None:
            author_id = user_id

        if author_id is None:
            raise HTTPException(
                status_code=400,
                detail="Author id is required"
            )

        thread_data = payload.model_dump(exclude={"tags"})
        thread_data["author_id"] = author_id

        thread = cls.repo.create(db, thread_data)
        raw_tags = payload.tags or []
        tag_names = sorted(
            {
                tag.strip().lower()
                for tag in raw_tags
                if isinstance(tag, str) and tag.strip()
            }
        )
        if tag_names:
            existing_tags = cls.tag_repo.get_by_names(db, tag_names)
            existing_by_name = {tag.name: tag for tag in existing_tags}
            to_create = [name for name in tag_names if name not in existing_by_name]

            created_tags = []
            for name in to_create:
                created_tags.append(
                    Tag(name=name)
                )
            if created_tags:
                db.add_all(created_tags)
                db.flush()

            thread.tags = [*existing_tags, *created_tags]
            db.commit()
            db.refresh(thread)

        author = cls.user_repo.get_by_id(db, author_id)
        if author is None or not cls._is_moderator_or_admin(author):
            ModerationService.create_review(
                db,
                ModerationCreate(
                    content_type="THREAD",
                    thread_id=thread.id,
                ),
            )
        mentioned_users = MentionService.process_mentions(
            db,
            f"{payload.title} {payload.description}",
            thread_id=thread.id,
        )
        actor_label = (
            (author.name or "").strip()
            if author is not None
            else ""
        ) or (author.email if author is not None else "") or "Someone"
        for user in mentioned_users:
            if user.id == author_id:
                continue
            NotificationService.create_notification(
                db,
                user_id=user.id,
                actor_id=author_id,
                type="THREAD_MENTION",
                title="You were mentioned in a thread",
                message=f"{actor_label} mentioned you in a thread.",
                entity_type="thread",
                entity_id=thread.id,
            )

        cls._invalidate_threads_cache()
        try:
            from_thread.run(
                broadcast_new_thread,
                thread,
                "created",
            )
        except Exception:
            # Realtime delivery is best-effort.
            pass
        return thread

    # ==============================
    # List Threads
    # ==============================
    @classmethod
    def list_threads(
        cls,
        db: Session,
        page: int = 1,
        size: int = 20,
        user_id: int | None = None,
    ):
        data: list[dict] | None = None

        if user_id is None:
            try:
                cached = cls._run_redis_call(
                    redis_client.redis.get,
                    cls._threads_cache_key
                )
                if cached:
                    data = json.loads(cached)
            except Exception:
                pass
        else:
            try:
                cached = cls._run_redis_call(
                    redis_client.redis.get,
                    cls._threads_cache_key
                )
                if cached:
                    data = json.loads(cached)
            except Exception:
                pass

        if data is None:
            threads = cls.repo.get_active_threads(db)
            # Cache canonical payload without user-specific like state.
            data = [cls._serialize_thread(thread, None) for thread in threads]

            try:
                cls._run_redis_call(
                    redis_client.redis.setex,
                    cls._threads_cache_key,
                    cls._threads_cache_ttl_seconds,
                    json.dumps(data, default=str),
                )
            except Exception:
                pass

        if user_id is not None:
            liked_thread_ids = cls.like_repo.get_liked_thread_ids(
                db,
                user_id,
            )
            for item in data:
                item["user_has_liked"] = (
                    int(item["id"]) in liked_thread_ids
                )

        total = len(data)
        pages = max(1, math.ceil(total / size))
        start = (page - 1) * size
        end = start + size
        return {
            "items": data[start:end],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    # ==============================
    # Get Thread
    # ==============================
    @classmethod
    def get_thread(
        cls,
        db: Session,
        thread_id: int,
        user_id: int | None = None,
    ):

        thread = cls.repo.get_by_id(db, thread_id)

        if not thread or thread.is_deleted:
            raise HTTPException(
                status_code=404,
                detail="Thread not found"
            )

        return cls._serialize_thread(thread, user_id)

    # ==============================
    # Update Thread
    # ==============================
    @classmethod
    def update_thread(
        cls,
        db: Session,
        thread_id: int,
        payload: ThreadUpdate,
        user_id: int,
        actor: User
    ):

        thread = cls.repo.get_by_id(db, thread_id)
        if not thread or thread.is_deleted:
            raise HTTPException(
                status_code=404,
                detail="Thread not found"
            )

        if (
            thread.author_id != user_id
            and not cls._is_moderator_or_admin(actor)
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed to edit"
            )

        payload_data = payload.model_dump(exclude_unset=True)
        new_tags = payload_data.pop("tags", None)

        updated_thread = cls.repo.update(
            db,
            thread,
            payload_data
        )
        if new_tags is not None:
            tag_names = sorted(
                {
                    tag.strip().lower()
                    for tag in new_tags
                    if isinstance(tag, str) and tag.strip()
                }
            )

            existing_tags = cls.tag_repo.get_by_names(db, tag_names)
            existing_by_name = {tag.name: tag for tag in existing_tags}
            to_create = [name for name in tag_names if name not in existing_by_name]

            created_tags = []
            for name in to_create:
                created_tags.append(
                    Tag(name=name)
                )
            if created_tags:
                db.add_all(created_tags)
                db.flush()

            updated_thread.tags = [*existing_tags, *created_tags]
            db.commit()
            db.refresh(updated_thread)
        cls._invalidate_threads_cache()
        try:
            from_thread.run(
                broadcast_new_thread,
                updated_thread,
                "updated",
            )
        except Exception:
            # Realtime delivery is best-effort.
            pass
        return cls._serialize_thread(updated_thread, user_id)

    # ==============================
    # Delete Thread (Soft)
    # ==============================
    @classmethod
    def delete_thread(
        cls,
        db: Session,
        thread_id: int,
        user_id: int,
        actor: User
    ):

        thread = cls.repo.get_by_id(db, thread_id)
        if not thread or thread.is_deleted:
            raise HTTPException(
                status_code=404,
                detail="Thread not found"
            )

        if (
            thread.author_id != user_id
            and not cls._is_moderator_or_admin(actor)
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed to delete"
            )

        cls.repo.soft_delete(
            db,
            thread,
        )
        cls._invalidate_threads_cache()
        try:
            from_thread.run(
                broadcast_new_thread,
                thread,
                "deleted",
            )
        except Exception:
            # Realtime delivery is best-effort.
            pass
