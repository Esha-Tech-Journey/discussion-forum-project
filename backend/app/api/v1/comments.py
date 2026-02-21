from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.comment import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
)
from app.schemas.base import MessageResponse
from app.services.comment_service import CommentService
from app.dependencies.auth import get_current_user
from app.dependencies.rate_limit import (
    comment_rate_limiter
)
from app.models.user import User


router = APIRouter(
    prefix="/comments",
    tags=["Comments"]
)


# ==============================
# Create Comment / Reply
# ==============================

@router.post(
    "",
    response_model=CommentResponse,
    dependencies=[Depends(comment_rate_limiter)]
)
def create_comment(
    payload: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    return CommentService.create_comment(
        db,
        payload,
        user.id
    )


# ==============================
# List Thread Comments
# ==============================

@router.get(
    "/thread/{thread_id}",
    response_model=list[CommentResponse]
)
def list_comments(
    thread_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    return CommentService.list_thread_comments(
        db,
        thread_id,
        page=page,
        size=size,
        user_id=user.id,
    )


# ==============================
# Update Comment
# ==============================

@router.put(
    "/{comment_id}",
    response_model=CommentResponse
)
def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    return CommentService.update_comment(
        db,
        comment_id,
        payload,
        user.id,
        user
    )


# ==============================
# Delete Comment
# ==============================

@router.delete(
    "/{comment_id}",
    response_model=MessageResponse,
)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    CommentService.delete_comment(
        db,
        comment_id,
        user.id,
        user
    )

    return {"message": "Comment deleted"}
