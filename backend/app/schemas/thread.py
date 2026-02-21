from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import TimestampSchema


# ==============================
# Create Thread
# ==============================

class ThreadCreate(BaseModel):
    title: str
    description: str
    tags: list[str] | None = None


# ==============================
# Update Thread
# ==============================

class ThreadUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None


class ThreadAuthor(BaseModel):
    id: int
    name: Optional[str] = None
    email: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==============================
# Thread Response
# ==============================

class ThreadResponse(TimestampSchema):
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)
    author_id: int
    author: Optional[ThreadAuthor] = None
    comment_count: int = 0
    like_count: int = 0
    user_has_liked: bool = False
    is_deleted: bool


class ThreadListResponse(BaseModel):
    items: list[ThreadResponse]
    total: int
    page: int
    size: int
    pages: int
