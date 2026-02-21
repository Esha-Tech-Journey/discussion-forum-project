from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.mention import MentionListResponse
from app.services.mention_service import MentionService


router = APIRouter(
    prefix="/mentions",
    tags=["Mentions"]
)


@router.get(
    "",
    response_model=MentionListResponse,
)
def list_mentions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return MentionService.get_user_mentions(
        db,
        user_id=user.id,
        page=page,
        size=size,
    )

