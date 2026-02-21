from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """
    User account model.

    Stores authentication credentials
    and profile metadata.
    """

    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    name = Column(String(150), nullable=True)
    avatar_url = Column(String, nullable=True)
    bio = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)

    # Relationships

    roles = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="joined",
    )

    threads = relationship("Thread", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    notifications = relationship(
        "Notification",
        foreign_keys="Notification.user_id",
        back_populates="user",
    )

    moderation_reviews = relationship(
        "ModerationReview",
        back_populates="reviewer"
    )

    mentions = relationship(
        "Mention",
        back_populates="mentioned_user"
    )
