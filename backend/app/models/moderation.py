from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ModerationReview(BaseModel):
    """
    Tracks moderation reviews on content.
    """

    __tablename__ = "moderation_reviews"

    content_type = Column(
        String(50),
        nullable=False
    )  # THREAD / COMMENT

    thread_id = Column(
        ForeignKey("threads.id"),
        nullable=True
    )

    comment_id = Column(
        ForeignKey("comments.id"),
        nullable=True
    )

    reason = Column(Text, nullable=True)

    reviewer_id = Column(
        ForeignKey("users.id"),
        nullable=True
    )

    status = Column(
        String(50),
        default="PENDING"
    )

    action_taken = Column(Text, nullable=True)

    # Relationships

    reviewer = relationship(
        "User",
        back_populates="moderation_reviews"
    )

    thread = relationship("Thread")
    comment = relationship("Comment")
