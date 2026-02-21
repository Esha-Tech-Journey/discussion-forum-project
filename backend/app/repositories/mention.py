from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.models.mention import Mention
from app.repositories.base import BaseRepository


class MentionRepository(BaseRepository[Mention]):

    def __init__(self):
        super().__init__(Mention)

    # Bulk create mentions
    def bulk_create(
        self,
        db: Session,
        mention_data: list[dict]
    ):

        mentions = [
            Mention(**data)
            for data in mention_data
        ]

        db.add_all(mentions)
        db.commit()

    def list_user_mentions(
        self,
        db: Session,
        user_id: int,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Mention], int]:
        offset = (page - 1) * size
        count_stmt = (
            select(func.count(Mention.id))
            .where(Mention.mentioned_user_id == user_id)
        )
        total = int(db.scalar(count_stmt) or 0)

        stmt = (
            select(Mention)
            .where(Mention.mentioned_user_id == user_id)
            .order_by(Mention.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        items = list(db.scalars(stmt).all())
        return items, total
