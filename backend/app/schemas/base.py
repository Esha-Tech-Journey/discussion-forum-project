from datetime import datetime
from pydantic import BaseModel, ConfigDict


class IDSchema(BaseModel):
    """
    Base response with ID.
    """
    id: int

    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(IDSchema):
    """
    Adds timestamp fields.
    """
    created_at: datetime
    updated_at: datetime


class SoftDeleteSchema(TimestampSchema):
    """
    Includes soft delete flag.
    """
    is_deleted: bool


class PaginationSchema(BaseModel):
    """
    Standard pagination response.
    """
    total: int
    page: int
    size: int


class MessageResponse(BaseModel):
    message: str
