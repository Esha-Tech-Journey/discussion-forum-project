from sqlalchemy import Column, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, SoftDeleteMixin


class Thread(BaseModel, SoftDeleteMixin):
    """
    Discussion thread model.
    """

    __tablename__ = "threads"

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    author_id = Column(
        ForeignKey("users.id"),
        nullable=False
    )

    # Relationships

    author = relationship(
        "User",
        back_populates="threads"
    )

    comments = relationship(
        "Comment",
        back_populates="thread",
        cascade="all, delete-orphan"
    )

    likes = relationship(
        "Like",
        back_populates="thread"
    )

    mentions = relationship(
        "Mention",
        back_populates="thread"
    )

    tags = relationship(
        "Tag",
        secondary="thread_tags"
    )


Index("idx_thread_title", Thread.title)
Index("idx_thread_description", Thread.description)
