from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base import TimestampSchema
from app.schemas.user import UserResponse


class ActivityTagCount(BaseModel):
    name: str
    count: int = Field(ge=0)


class ActivityThreadItem(TimestampSchema):
    id: int
    title: str
    tags: list[str] = []
    like_count: int = Field(ge=0)
    comment_count: int = Field(ge=0)


class ActivityCommentItem(TimestampSchema):
    id: int
    content: str
    thread_id: int
    thread_title: Optional[str] = None
    like_count: int = Field(ge=0)


class ActivityLikeItem(TimestampSchema):
    id: int
    target_type: str
    thread_id: Optional[int] = None
    thread_title: Optional[str] = None
    comment_id: Optional[int] = None
    comment_excerpt: Optional[str] = None


class UserActivityStats(BaseModel):
    threads: int = Field(ge=0)
    comments: int = Field(ge=0)
    likes_given: int = Field(ge=0)
    likes_received: int = Field(ge=0)


class UserActivityResponse(BaseModel):
    user: UserResponse
    stats: UserActivityStats
    top_tags: list[ActivityTagCount] = []
    recent_threads: list[ActivityThreadItem] = []
    recent_comments: list[ActivityCommentItem] = []
    recent_likes: list[ActivityLikeItem] = []

