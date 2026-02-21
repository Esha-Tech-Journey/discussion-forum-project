from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    def __init__(self):
        super().__init__(Tag)

    def get_by_names(
        self,
        db: Session,
        names: list[str],
    ) -> list[Tag]:
        if not names:
            return []

        stmt = select(Tag).where(Tag.name.in_(names))
        return list(db.scalars(stmt).all())

