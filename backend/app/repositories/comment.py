from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.models.comment import Comment
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):

    def __init__(self):
        super().__init__(Comment)

    # ==============================
    # Get thread comments
    # ==============================
    def get_thread_comments(
        self,
        db: Session,
        thread_id: int,
        page: int = 1,
        size: int = 100,
    ):
        offset = (page - 1) * size

        stmt = select(Comment).where(
            Comment.thread_id == thread_id
        ).options(
            selectinload(Comment.author),
            selectinload(Comment.likes),
        ).order_by(
            Comment.created_at.asc()
        ).offset(
            offset
        ).limit(
            size
        )

        return list(db.scalars(stmt).all())

    def soft_delete(
        self,
        db: Session,
        comment: Comment
    ) -> Comment:
        comment.is_deleted = True
        db.commit()
        db.refresh(comment)
        return comment

    def search_comments(
        self,
        db: Session,
        keyword: str,
    ) -> list[Comment]:
        stmt = (
            select(Comment)
            .where(
                Comment.is_deleted == False,
                Comment.content.ilike(f"%{keyword}%"),
            )
            .options(
                selectinload(Comment.author),
                selectinload(Comment.likes),
            )
            .order_by(Comment.created_at.desc())
        )
        return list(db.scalars(stmt).all())
