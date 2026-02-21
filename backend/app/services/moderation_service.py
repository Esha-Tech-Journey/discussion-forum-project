from sqlalchemy.orm import Session
from fastapi import HTTPException
from anyio import from_thread

from app.schemas.moderation import (
    ModerationCreate,
    ReportCreate,
    ModerationUpdate,
)
from app.repositories.moderation import (
    ModerationRepository
)
from app.websocket.handlers import broadcast_moderation_review


class ModerationService:

    repo = ModerationRepository()

    # ==============================
    # Create Review
    # ==============================
    @classmethod
    def create_review(
        cls,
        db: Session,
        payload: ModerationCreate | ReportCreate
    ):
        review = cls.repo.create(
            db,
            payload.model_dump()
        )

        try:
            from_thread.run(
                broadcast_moderation_review,
                review,
                "created",
            )
        except Exception:
            # Realtime delivery is best-effort.
            pass

        return review

    # ==============================
    # List Pending
    # ==============================
    @classmethod
    def list_pending_reviews(
        cls,
        db: Session
    ):

        return cls.repo.get_pending_reviews(db)

    @classmethod
    def list_completed_reviews(
        cls,
        db: Session
    ):
        return cls.repo.get_completed_reviews(db)

    # ==============================
    # Update Review Status
    # ==============================
    @classmethod
    def update_review(
        cls,
        db: Session,
        review_id: int,
        payload: ModerationUpdate,
        reviewer_id: int
    ):

        review = cls.repo.get_by_id(db, review_id)

        if not review:
            raise HTTPException(404, "Review not found")

        update_data = payload.model_dump()
        update_data["reviewer_id"] = reviewer_id

        updated_review = cls.repo.update(
            db,
            review,
            update_data
        )
        try:
            from_thread.run(
                broadcast_moderation_review,
                updated_review,
                "updated",
            )
        except Exception:
            # Realtime delivery is best-effort.
            pass

        return updated_review
