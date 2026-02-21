from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.notification import (
    NotificationListResponse,
    NotificationMarkAllReadResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.services.notification_service import (
    NotificationService,
)
from app.dependencies.auth import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


# ==============================
# List Notifications
# ==============================

@router.get(
    "",
    response_model=NotificationListResponse
)
def get_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    return NotificationService.get_user_notifications(
        db,
        user.id,
        page=page,
        size=size,
    )


# ==============================
# Mark Read
# ==============================

@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse
)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    return NotificationService.mark_as_read(
        db,
        user.id,
        notification_id
    )


@router.patch(
    "/read-all",
    response_model=NotificationMarkAllReadResponse,
)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    updated = NotificationService.mark_all_as_read(
        db,
        user.id,
    )
    return {"updated": updated}


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountResponse,
)
def get_unread_count(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    unread_count = NotificationService.get_unread_count(
        db,
        user.id,
    )
    return {"unread_count": unread_count}
