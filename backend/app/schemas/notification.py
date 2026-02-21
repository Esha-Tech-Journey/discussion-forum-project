from pydantic import BaseModel, Field

from app.schemas.base import TimestampSchema


class NotificationResponse(TimestampSchema):
    user_id: int
    actor_id: int | None
    type: str
    title: str
    message: str
    entity_type: str
    entity_id: int
    is_read: bool


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    size: int


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationMarkAllReadResponse(BaseModel):
    updated: int = Field(ge=0)
