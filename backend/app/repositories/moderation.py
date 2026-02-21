from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.moderation import ModerationReview
from app.repositories.base import BaseRepository


class ModerationRepository(
    BaseRepository[ModerationReview]
):

    def __init__(self):
        super().__init__(ModerationReview)

    # ==============================
    # Get pending reviews
    # ==============================
    def get_pending_reviews(
        self,
        db: Session
    ):
        stmt = select(ModerationReview).where(
            ModerationReview.status == "PENDING"
        )

        return list(db.scalars(stmt).all())

    def get_completed_reviews(
        self,
        db: Session
    ):
        stmt = select(ModerationReview).where(
            ModerationReview.status == "COMPLETED"
        )
        return list(db.scalars(stmt).all())
