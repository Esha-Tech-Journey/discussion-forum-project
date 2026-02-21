from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime, Boolean
from app.db.base import Base


class IDMixin:
    """
    Provides primary key ID column.
    """
    id = Column(Integer, primary_key=True, index=True)


class TimestampMixin:
    """
    Adds created & updated timestamps.
    """
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class SoftDeleteMixin:
    """
    Enables soft delete functionality.
    """
    is_deleted = Column(Boolean, default=False)


class BaseModel(Base, IDMixin, TimestampMixin):
    """
    Base model combining ID + timestamps.
    All core models inherit from this.
    """
    __abstract__ = True
