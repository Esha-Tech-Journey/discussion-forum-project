from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.thread import Thread
from app.models.comment import Comment
from app.models.like import Like
from app.models.role import Role, user_roles
from app.models.tag import Tag
from app.models.thread_tag import ThreadTag
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):

    def __init__(self):
        super().__init__(User)

    def get_by_email(
        self,
        db: Session,
        email: str
    ):

        return (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    def get_active_by_id(
        self,
        db: Session,
        user_id: int,
    ) -> User | None:
        stmt = select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
        )
        return db.scalar(stmt)

    def get_by_names(
        self,
        db: Session,
        names: list[str]
    ) -> list[User]:
        if not names:
            return []

        stmt = select(User).where(
            User.name.in_(names)
        )
        # User.roles is joined-eager-loaded; use unique() to dedupe rows.
        return list(db.execute(stmt).unique().scalars().all())

    def create_with_roles(
        self,
        db: Session,
        user_data: dict,
        roles: list
    ) -> User:
        user = User(**user_data)
        for role in roles:
            user.roles.append(role)

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def list_users(
        self,
        db: Session,
        page: int,
        size: int,
        q: str | None = None,
    ) -> tuple[list[User], int]:
        stmt = select(User)
        count_stmt = select(func.count()).select_from(User)

        if q:
            query = f"%{q}%"
            stmt = stmt.where(
                User.email.ilike(query)
                | User.name.ilike(query)
            )
            count_stmt = count_stmt.where(
                User.email.ilike(query)
                | User.name.ilike(query)
            )

        total = int(db.scalar(count_stmt) or 0)
        offset = (page - 1) * size
        result = db.execute(
            stmt.offset(offset).limit(size)
        )
        items = list(
            result.unique().scalars().all()
        )
        return items, total

    def list_users_by_role_with_stats(
        self,
        db: Session,
        role_name: str,
        page: int,
        size: int,
        q: str | None = None,
    ) -> tuple[list[dict], int]:
        thread_count = func.count(func.distinct(Thread.id))
        received_like_count = func.count(Like.id)
        role_filter = (
            or_(Role.role_name == role_name, Role.id.is_(None))
            if role_name == "MEMBER"
            else Role.role_name == role_name
        )

        stmt = (
            select(
                User,
                thread_count.label("thread_count"),
                received_like_count.label("received_like_count"),
            )
            .outerjoin(user_roles, user_roles.c.user_id == User.id)
            .outerjoin(Role, Role.id == user_roles.c.role_id)
            .outerjoin(
                Thread,
                (Thread.author_id == User.id) & (Thread.is_deleted == False),
            )
            .outerjoin(Like, Like.thread_id == Thread.id)
            .where(
                role_filter,
            )
            .group_by(User.id)
            .order_by(User.created_at.desc())
        )

        count_stmt = (
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .outerjoin(user_roles, user_roles.c.user_id == User.id)
            .outerjoin(Role, Role.id == user_roles.c.role_id)
            .where(
                role_filter,
            )
        )

        if q:
            query = f"%{q}%"
            user_filter = User.email.ilike(query) | User.name.ilike(query)
            stmt = stmt.where(user_filter)
            count_stmt = count_stmt.where(user_filter)

        total = int(db.scalar(count_stmt) or 0)
        offset = (page - 1) * size
        rows = db.execute(stmt.offset(offset).limit(size)).unique().all()

        items: list[dict] = []
        for user, user_thread_count, user_received_like_count in rows:
            items.append(
                {
                    "id": user.id,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                    "email": user.email,
                    "name": user.name,
                    "avatar_url": user.avatar_url,
                    "is_active": user.is_active,
                    "roles": [
                        {
                            "id": role.id,
                            "role_name": role.role_name,
                        }
                        for role in (user.roles or [])
                    ],
                    "thread_count": int(user_thread_count or 0),
                    "received_like_count": int(user_received_like_count or 0),
                }
            )

        return items, total

    def suggest_users(
        self,
        db: Session,
        q: str | None = None,
        limit: int = 8,
        exclude_user_id: int | None = None,
    ) -> list[User]:
        stmt = select(User).where(
            User.is_active.is_(True),
            User.name.is_not(None),
            func.length(func.trim(User.name)) > 0,
        )

        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)

        if q:
            # Prefix match for "typeahead" UX.
            stmt = stmt.where(User.name.ilike(f"{q}%"))

        stmt = stmt.order_by(User.name.asc()).limit(limit)
        # User.roles is joined-eager-loaded; use unique() to dedupe rows.
        return list(db.execute(stmt).unique().scalars().all())

    def get_user_activity_snapshot(
        self,
        db: Session,
        target_user_id: int,
        limit_threads: int = 10,
        limit_comments: int = 10,
        limit_likes: int = 10,
    ) -> dict:
        threads_count = int(db.scalar(
            select(func.count(Thread.id)).where(
                Thread.author_id == target_user_id,
                Thread.is_deleted.is_(False),
            )
        ) or 0)
        comments_count = int(db.scalar(
            select(func.count(Comment.id)).where(
                Comment.author_id == target_user_id,
                Comment.is_deleted.is_(False),
            )
        ) or 0)
        likes_given_count = int(db.scalar(
            select(func.count(Like.id)).where(Like.user_id == target_user_id)
        ) or 0)

        likes_on_threads = (
            select(func.count(Like.id))
            .select_from(Like)
            .join(Thread, Thread.id == Like.thread_id)
            .where(
                Thread.author_id == target_user_id,
                Thread.is_deleted.is_(False),
                Like.user_id != target_user_id,
            )
        )
        likes_on_comments = (
            select(func.count(Like.id))
            .select_from(Like)
            .join(Comment, Comment.id == Like.comment_id)
            .where(
                Comment.author_id == target_user_id,
                Comment.is_deleted.is_(False),
                Like.user_id != target_user_id,
            )
        )
        likes_received_count = int((db.scalar(likes_on_threads) or 0) + (db.scalar(likes_on_comments) or 0))

        tag_rows = db.execute(
            select(
                Tag.name,
                func.count(Tag.id).label("cnt"),
            )
            .select_from(ThreadTag)
            .join(Tag, Tag.id == ThreadTag.tag_id)
            .join(Thread, Thread.id == ThreadTag.thread_id)
            .where(
                Thread.author_id == target_user_id,
                Thread.is_deleted.is_(False),
            )
            .group_by(Tag.name)
            .order_by(desc("cnt"))
            .limit(10)
        ).all()
        top_tags = [{"name": name, "count": int(cnt or 0)} for name, cnt in tag_rows]

        threads = list(db.scalars(
            select(Thread)
            .options(
                selectinload(Thread.tags),
                selectinload(Thread.likes),
                selectinload(Thread.comments),
            )
            .where(
                Thread.author_id == target_user_id,
                Thread.is_deleted.is_(False),
            )
            .order_by(Thread.created_at.desc())
            .limit(limit_threads)
        ).all())

        recent_threads = []
        for thread in threads:
            recent_threads.append({
                "id": thread.id,
                "created_at": thread.created_at,
                "updated_at": thread.updated_at,
                "title": thread.title,
                "tags": [t.name for t in (thread.tags or [])],
                "like_count": len(list(thread.likes or [])),
                "comment_count": sum(1 for c in (thread.comments or []) if not c.is_deleted),
            })

        comment_rows = db.execute(
            select(Comment, Thread.title)
            .join(Thread, Thread.id == Comment.thread_id)
            .options(
                selectinload(Comment.likes),
            )
            .where(
                Comment.author_id == target_user_id,
                Comment.is_deleted.is_(False),
            )
            .order_by(Comment.created_at.desc())
            .limit(limit_comments)
        ).unique().all()

        recent_comments = []
        for comment, thread_title in comment_rows:
            recent_comments.append({
                "id": comment.id,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "content": comment.content,
                "thread_id": comment.thread_id,
                "thread_title": thread_title,
                "like_count": len(list(comment.likes or [])),
            })

        likes = list(db.scalars(
            select(Like)
            .options(
                selectinload(Like.thread).selectinload(Thread.tags),
                selectinload(Like.comment).selectinload(Comment.thread),
            )
            .where(Like.user_id == target_user_id)
            .order_by(Like.created_at.desc())
            .limit(limit_likes)
        ).all())

        recent_likes = []
        for like in likes:
            if like.thread_id and like.thread is not None:
                recent_likes.append({
                    "id": like.id,
                    "created_at": like.created_at,
                    "updated_at": like.updated_at,
                    "target_type": "thread",
                    "thread_id": like.thread_id,
                    "thread_title": like.thread.title,
                    "comment_id": None,
                    "comment_excerpt": None,
                })
            elif like.comment_id and like.comment is not None:
                excerpt = (like.comment.content or "").strip()
                if len(excerpt) > 120:
                    excerpt = excerpt[:117] + "..."
                recent_likes.append({
                    "id": like.id,
                    "created_at": like.created_at,
                    "updated_at": like.updated_at,
                    "target_type": "comment",
                    "thread_id": like.comment.thread_id,
                    "thread_title": like.comment.thread.title if like.comment.thread else None,
                    "comment_id": like.comment_id,
                    "comment_excerpt": excerpt,
                })

        return {
            "stats": {
                "threads": threads_count,
                "comments": comments_count,
                "likes_given": likes_given_count,
                "likes_received": likes_received_count,
            },
            "top_tags": top_tags,
            "recent_threads": recent_threads,
            "recent_comments": recent_comments,
            "recent_likes": recent_likes,
        }
