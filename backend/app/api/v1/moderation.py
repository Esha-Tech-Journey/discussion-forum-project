from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.moderation import (
    ModerationCreate,
    ReportCreate,
    ModerationResponse,
    ModerationUpdate,
)
from app.services.moderation_service import (
    ModerationService,
)
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import (
    require_moderator,
)
from app.models.user import User


router = APIRouter(
    prefix="/moderation",
    tags=["Moderation"]
)


# ==============================
# Create Review
# ==============================

@router.post(
    "",
    response_model=ModerationResponse
)
def create_review(
    payload: ModerationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):

    return ModerationService.create_review(
        db,
        payload
    )


@router.post(
    "/report",
    response_model=ModerationResponse
)
def report_content(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):

    return ModerationService.create_review(
        db,
        payload
    )


# ==============================
# Pending Reviews
# ==============================

@router.get(
    "/pending",
    response_model=list[ModerationResponse]
)
def get_pending_reviews(
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):

    return ModerationService.list_pending_reviews(
        db
    )


@router.get(
    "/completed",
    response_model=list[ModerationResponse]
)
def get_completed_reviews(
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    return ModerationService.list_completed_reviews(
        db
    )


# ==============================
# Update Review
# ==============================

@router.put(
    "/{review_id}",
    response_model=ModerationResponse
)
def update_review(
    review_id: int,
    payload: ModerationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_moderator),
):

    return ModerationService.update_review(
        db,
        review_id,
        payload,
        user.id
    )


@router.post(
    "/{review_id}/action",
    response_model=ModerationResponse
)
def take_action_on_review(
    review_id: int,
    payload: ModerationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_moderator),
):
    return ModerationService.update_review(
        db,
        review_id,
        payload,
        user.id
    )
