from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.like import Like
from app.repositories.base import BaseRepository


class LikeRepository(BaseRepository[Like]):

    def __init__(self):
        super().__init__(Like)

    # ==============================
    # Check existing like
    # ==============================
    def get_user_like(
        self,
        db: Session,
        user_id: int,
        thread_id=None,
        comment_id=None
    ):

        stmt = select(Like).where(
            Like.user_id == user_id,
            Like.thread_id == thread_id,
            Like.comment_id == comment_id
        )

        return db.scalar(stmt)

    # ==============================
    # Count likes
    # ==============================
    def count_thread_likes(
        self,
        db: Session,
        thread_id: int
    ):
        return db.query(Like).filter(
            Like.thread_id == thread_id
        ).count()

    def count_comment_likes(
        self,
        db: Session,
        comment_id: int
    ):
        return db.query(Like).filter(
            Like.comment_id == comment_id
        ).count()

    def get_liked_thread_ids(
        self,
        db: Session,
        user_id: int,
    ) -> set[int]:
        stmt = select(Like.thread_id).where(
            Like.user_id == user_id,
            Like.thread_id.is_not(None),
        )
        return {
            int(thread_id)
            for thread_id in db.scalars(stmt).all()
            if thread_id is not None
        }

    def remove_like(
        self,
        db: Session,
        like: Like
    ) -> None:
        self.delete(db, like)
