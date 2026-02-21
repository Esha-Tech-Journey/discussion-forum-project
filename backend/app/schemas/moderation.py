from typing import Optional

from pydantic import BaseModel

from app.schemas.base import TimestampSchema


# ==============================
# Create Review
# ==============================

class ModerationCreate(BaseModel):
    content_type: str
    thread_id: Optional[int] = None
    comment_id: Optional[int] = None


class ReportCreate(BaseModel):
    content_type: str
    thread_id: Optional[int] = None
    comment_id: Optional[int] = None
    reason: str


# ==============================
# Update Review
# ==============================

class ModerationUpdate(BaseModel):
    status: str
    action_taken: Optional[str] = None


# ==============================
# Response
# ==============================

class ModerationResponse(TimestampSchema):
    content_type: str
    thread_id: Optional[int]
    comment_id: Optional[int]
    reason: Optional[str]
    reviewer_id: Optional[int]
    status: str
    action_taken: Optional[str]
