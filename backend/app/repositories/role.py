from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.role import Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):

    def __init__(self):
        super().__init__(Role)

    def get_by_name(
        self,
        db: Session,
        role_name: str
    ) -> Role | None:
        stmt = select(Role).where(
            Role.role_name == role_name
        )
        return db.scalar(stmt)

    def get_by_names(
        self,
        db: Session,
        role_names: list[str],
    ) -> list[Role]:
        if not role_names:
            return []
        stmt = select(Role).where(
            Role.role_name.in_(role_names)
        )
        return list(db.scalars(stmt).all())
