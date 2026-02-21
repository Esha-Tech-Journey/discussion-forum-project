from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Notification(BaseModel):
    """
    Stores user notifications.
    """

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_is_read", "is_read"),
        Index("ix_notifications_created_at", "created_at"),
    )

    user_id = Column(
        ForeignKey("users.id"),
        nullable=False
    )

    actor_id = Column(
        ForeignKey("users.id"),
        nullable=True
    )

    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)

    is_read = Column(Boolean, default=False, nullable=False)

    # Relationships

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="notifications"
    )

    actor = relationship(
        "User",
        foreign_keys=[actor_id]
    )
