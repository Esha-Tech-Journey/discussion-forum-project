from typing import Optional, List

from pydantic import BaseModel

from app.schemas.base import TimestampSchema
from app.schemas.thread import ThreadAuthor


# ==============================
# Create Comment
# ==============================

class CommentCreate(BaseModel):
    thread_id: int
    content: str
    parent_comment_id: Optional[int] = None


# ==============================
# Update Comment
# ==============================

class CommentUpdate(BaseModel):
    content: str


# ==============================
# Comment Response
# ==============================

class CommentResponse(TimestampSchema):
    content: str
    thread_id: int
    author_id: int
    author: Optional[ThreadAuthor] = None
    parent_comment_id: Optional[int]
    like_count: int = 0
    user_has_liked: bool = False
    is_deleted: bool
