from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, func, or_, select

from app.models.thread import Thread
from app.models.tag import Tag
from app.repositories.base import BaseRepository


class ThreadRepository(BaseRepository[Thread]):

    def __init__(self):
        super().__init__(Thread)

    # Custom query
    def get_active_threads(self, db: Session):
        stmt = (
            select(Thread)
            .options(
                selectinload(Thread.author),
                selectinload(Thread.tags),
                selectinload(Thread.likes),
                selectinload(Thread.comments),
            )
            .where(
            Thread.is_deleted == False
            )
            .order_by(desc(Thread.created_at))
        )
        return list(db.scalars(stmt).all())

    def get_by_id(
        self,
        db: Session,
        obj_id: int
    ) -> Thread | None:
        stmt = (
            select(Thread)
            .options(
                selectinload(Thread.author),
                selectinload(Thread.tags),
                selectinload(Thread.likes),
                selectinload(Thread.comments),
            )
            .where(Thread.id == obj_id)
        )
        return db.scalar(stmt)

    def count_active_threads(self, db: Session) -> int:
        stmt = select(func.count()).select_from(Thread).where(
            Thread.is_deleted == False
        )
        return int(db.scalar(stmt) or 0)

    def search_threads(
        self,
        db: Session,
        keyword: str,
        search_in: str = "all",
    ):
        filters = []
        if search_in == "title":
            filters.append(
                Thread.title.ilike(f"%{keyword}%")
            )
        elif search_in == "content":
            filters.append(
                Thread.description.ilike(f"%{keyword}%")
            )
        elif search_in == "tags":
            filters.append(
                Thread.tags.any(
                    Tag.name.ilike(f"%{keyword}%")
                )
            )
        else:
            filters.append(
                or_(
                    Thread.title.ilike(f"%{keyword}%"),
                    Thread.description.ilike(f"%{keyword}%"),
                    Thread.tags.any(
                        Tag.name.ilike(f"%{keyword}%")
                    ),
                )
            )

        stmt = (
            select(Thread)
            .options(
                selectinload(Thread.author),
                selectinload(Thread.tags),
                selectinload(Thread.likes),
                selectinload(Thread.comments),
            )
            .where(
                Thread.is_deleted == False,
                *filters,
            )
        )

        results = list(db.scalars(stmt).all())

        return results

    def soft_delete(
        self,
        db: Session,
        thread: Thread
    ) -> Thread:
        thread.is_deleted = True
        db.commit()
        db.refresh(thread)
        return thread
