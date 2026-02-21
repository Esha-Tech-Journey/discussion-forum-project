from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Mention(BaseModel):
    """
    Stores @username mentions inside content.
    """

    __tablename__ = "mentions"

    mentioned_user_id = Column(
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

    # Relationships

    mentioned_user = relationship(
        "User",
        back_populates="mentions"
    )

    thread = relationship(
        "Thread",
        back_populates="mentions"
    )

    comment = relationship(
        "Comment",
        back_populates="mentions"
    )
