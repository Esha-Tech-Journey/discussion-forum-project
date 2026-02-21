from typing import Optional

from pydantic import BaseModel

from app.schemas.base import TimestampSchema


# ==============================
# Like Request
# ==============================

class LikeCreate(BaseModel):
    thread_id: Optional[int] = None
    comment_id: Optional[int] = None


# ==============================
# Like Response
# ==============================

class LikeResponse(TimestampSchema):
    user_id: int
    thread_id: Optional[int]
    comment_id: Optional[int]
