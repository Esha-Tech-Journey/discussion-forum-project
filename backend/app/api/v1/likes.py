from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.like import (
    LikeCreate,
    LikeResponse,
)
from app.schemas.base import MessageResponse
from app.services.like_service import LikeService
from app.dependencies.auth import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/likes",
    tags=["Likes"]
)


# ==============================
# Add Like
# ==============================

@router.post(
    "",
    response_model=LikeResponse
)
def add_like(
    payload: LikeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    return LikeService.add_like(
        db,
        payload,
        user.id
    )


# ==============================
# Remove Like
# ==============================

@router.delete(
    "",
    response_model=MessageResponse,
)
def remove_like(
    payload: LikeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    LikeService.remove_like(
        db,
        payload,
        user.id
    )

    return {"message": "Like removed"}
