from sqlalchemy import Column, ForeignKey

from app.db.base import Base


class ThreadTag(Base):

    __tablename__ = "thread_tags"

    thread_id = Column(
        ForeignKey("threads.id"),
        primary_key=True
    )

    tag_id = Column(
        ForeignKey("tags.id"),
        primary_key=True
    )
