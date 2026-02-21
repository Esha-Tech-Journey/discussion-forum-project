from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Like(BaseModel):
    """
    Like model supporting threads & comments.
    """

    __tablename__ = "likes"

    user_id = Column(
        ForeignKey("users.id"),
        nullable=False
    )

    thread_id = Column(
        ForeignKey("threads.id"),
        nullable=True
    )

    comment_id = Column(
        ForeignKey("comments.id"),
        nullable=True
    )

    # Ensure one like per user per target
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "thread_id",
            name="unique_user_thread_like"
        ),
        UniqueConstraint(
            "user_id",
            "comment_id",
            name="unique_user_comment_like"
        ),
    )

    # Relationships

    user = relationship("User")

    thread = relationship(
        "Thread",
        back_populates="likes"
    )

    comment = relationship(
        "Comment",
        back_populates="likes"
    )
