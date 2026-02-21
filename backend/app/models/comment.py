from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, SoftDeleteMixin


class Comment(BaseModel, SoftDeleteMixin):
    """
    Thread comment with nested replies support.
    """

    __tablename__ = "comments"

    content = Column(Text, nullable=False)

    thread_id = Column(
        ForeignKey("threads.id"),
        nullable=False
    )

    author_id = Column(
        ForeignKey("users.id"),
        nullable=False
    )

    parent_comment_id = Column(
        ForeignKey("comments.id"),
        nullable=True
    )

    # Relationships

    thread = relationship(
        "Thread",
        back_populates="comments"
    )

    author = relationship(
        "User",
        back_populates="comments"
    )

    parent = relationship(
        "Comment",
        remote_side="Comment.id",
        back_populates="replies"
    )

    replies = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    likes = relationship(
        "Like",
        back_populates="comment"
    )

    mentions = relationship(
        "Mention",
        back_populates="comment"
    )
