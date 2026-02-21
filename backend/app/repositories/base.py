from typing import Type, Generic, TypeVar, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing CRUD operations.
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    # CREATE
    def create(self, db: Session, obj_data: dict) -> ModelType:
        obj = self.model(**obj_data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    # GET BY ID
    def get_by_id(self, db: Session, obj_id: int) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == obj_id)
        return db.scalar(stmt)

    # LIST ALL
    def list_all(self, db: Session) -> List[ModelType]:
        stmt = select(self.model)
        return list(db.scalars(stmt).all())

    # UPDATE
    def update(
        self,
        db: Session,
        db_obj: ModelType,
        update_data: dict
    ) -> ModelType:

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    # DELETE (Soft or Hard depending on model)
    def delete(self, db: Session, db_obj: ModelType) -> None:
        db.delete(db_obj)
        db.commit()
