import math
import logging
from anyio import from_thread

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.constants import Roles
from app.models.user import User
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.services.notification_service import NotificationService
from app.websocket.handlers import broadcast_new_user


class UserService:

    repo = UserRepository()
    role_repo = RoleRepository()
    logger = logging.getLogger(__name__)

    @staticmethod
    def _is_admin(user: User) -> bool:
        return any(
            role.role_name == Roles.ADMIN
            for role in user.roles
        )

    @classmethod
    def get_profile(
        cls,
        db: Session,
        user_id: int
    ):

        return cls.repo.get_by_id(db, user_id)

    @classmethod
    def update_profile(
        cls,
        db: Session,
        user_id: int,
        data: dict
    ):

        user = cls.repo.get_by_id(db, user_id)

        return cls.repo.update(db, user, data)

    @classmethod
    def list_users(
        cls,
        db: Session,
        page: int = 1,
        size: int = 20,
        q: str | None = None,
    ):
        items, total = cls.repo.list_users(
            db,
            page=page,
            size=size,
            q=q,
        )
        pages = max(1, math.ceil(total / size))
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    @classmethod
    def list_users_by_role_with_stats(
        cls,
        db: Session,
        role_name: str,
        page: int = 1,
        size: int = 20,
        q: str | None = None,
    ):
        if role_name not in {Roles.MEMBER, Roles.MODERATOR}:
            raise HTTPException(400, "Unsupported role for this view")

        items, total = cls.repo.list_users_by_role_with_stats(
            db,
            role_name=role_name,
            page=page,
            size=size,
            q=q,
        )
        pages = max(1, math.ceil(total / size))
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    @classmethod
    def update_user(
        cls,
        db: Session,
        actor: User,
        user_id: int,
        data: dict,
    ):
        if not cls._is_admin(actor):
            raise HTTPException(403, "Admin required")

        user = cls.repo.get_by_id(db, user_id)
        if not user:
            raise HTTPException(404, "User not found")

        updated_user = cls.repo.update(db, user, data)

        try:
            from_thread.run(
                broadcast_new_user,
                updated_user,
                "updated",
            )
        except Exception:
            # Realtime delivery is best-effort.
            cls.logger.warning(
                "Failed to broadcast updated user event for user_id=%s",
                updated_user.id,
                exc_info=True,
            )

        return updated_user

    @classmethod
    def set_user_role(
        cls,
        db: Session,
        actor: User,
        user_id: int,
        role_name: str,
    ):
        if not cls._is_admin(actor):
            raise HTTPException(403, "Admin required")

        user = cls.repo.get_by_id(db, user_id)
        if not user:
            raise HTTPException(404, "User not found")

        role = cls.role_repo.get_by_name(db, role_name)
        if not role:
            raise HTTPException(400, "Role not found")

        previous_roles = {r.role_name for r in user.roles}
        user.roles = [role]
        db.commit()
        db.refresh(user)

        try:
            from_thread.run(
                broadcast_new_user,
                user,
                "updated",
            )
        except Exception:
            # Realtime delivery is best-effort.
            cls.logger.warning(
                "Failed to broadcast role update event for user_id=%s",
                user.id,
                exc_info=True,
            )

        if role_name == Roles.ADMIN and Roles.ADMIN not in previous_roles:
            NotificationService.create_notification(
                db,
                user_id=user.id,
                actor_id=actor.id,
                type="ROLE_PROMOTION",
                title="You have been promoted to Admin",
                message="Re-login to access the admin dashboard.",
                entity_type="user",
                entity_id=user.id,
            )

        if (
            role_name == Roles.MODERATOR
            and Roles.MODERATOR not in previous_roles
        ):
            NotificationService.create_notification(
                db,
                user_id=user.id,
                actor_id=actor.id,
                type="ROLE_PROMOTION",
                title="You have been promoted to Moderator",
                message="Please login as moderator to access moderator dashboard.",
                entity_type="user",
                entity_id=user.id,
            )

        return user

    @classmethod
    def suggest_users(
        cls,
        db: Session,
        q: str | None,
        limit: int,
        exclude_user_id: int | None = None,
    ):
        # Keep this endpoint lightweight and safe for general authenticated use.
        return cls.repo.suggest_users(
            db,
            q=(q or "").strip() or None,
            limit=limit,
            exclude_user_id=exclude_user_id,
        )

    @classmethod
    def get_user_activity(
        cls,
        db: Session,
        actor: User,
        target_user_id: int,
        limit_threads: int = 10,
        limit_comments: int = 10,
        limit_likes: int = 10,
    ):
        if not cls._is_admin(actor):
            raise HTTPException(403, "Admin required")

        target = cls.repo.get_by_id(db, target_user_id)
        if not target:
            raise HTTPException(404, "User not found")

        snapshot = cls.repo.get_user_activity_snapshot(
            db,
            target_user_id=target_user_id,
            limit_threads=limit_threads,
            limit_comments=limit_comments,
            limit_likes=limit_likes,
        )

        return {
            "user": target,
            "stats": snapshot["stats"],
            "top_tags": snapshot["top_tags"],
            "recent_threads": snapshot["recent_threads"],
            "recent_comments": snapshot["recent_comments"],
            "recent_likes": snapshot["recent_likes"],
        }
