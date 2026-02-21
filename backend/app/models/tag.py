from sqlalchemy import Column, String

from app.models.base import BaseModel


class Tag(BaseModel):

    __tablename__ = "tags"

    name = Column(String, unique=True)
