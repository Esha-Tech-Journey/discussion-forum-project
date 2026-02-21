from typing import Optional

from pydantic import BaseModel

from app.schemas.base import TimestampSchema


class MentionResponse(TimestampSchema):
    mentioned_user_id: int
    thread_id: Optional[int]
    comment_id: Optional[int]


class MentionListResponse(BaseModel):
    items: list[MentionResponse]
    total: int
    page: int
    size: int
