from typing import List

from pydantic import BaseModel

from app.schemas.thread import ThreadResponse
from app.schemas.comment import CommentResponse


class ThreadSearchResponse(BaseModel):
    """
    Search result wrapper.
    """

    results: List[ThreadResponse]
    total: int


class CommentSearchResponse(BaseModel):
    results: List[CommentResponse]
    total: int
