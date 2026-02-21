from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.thread import (
    ThreadCreate,
    ThreadListResponse,
    ThreadResponse,
    ThreadUpdate,
)
from app.schemas.base import MessageResponse
from app.services.thread_service import ThreadService
from app.dependencies.auth import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/threads",
    tags=["Threads"]
)


# ==============================
# Create Thread
# ==============================

@router.post(
    "",
    response_model=ThreadResponse
)
def create_thread(
    payload: ThreadCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    return ThreadService.create_thread(
        db,
        payload,
        user.id
    )


# ==============================
# List Threads
# ==============================

@router.get(
    "",
    response_model=ThreadListResponse
)
def list_threads(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ThreadService.list_threads(
        db,
        page=page,
        size=size,
        user_id=user.id,
    )


# ==============================
# Get Thread
# ==============================

@router.get(
    "/{thread_id}",
    response_model=ThreadResponse
)
def get_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ThreadService.get_thread(
        db,
        thread_id,
        user_id=user.id,
    )


# ==============================
# Update Thread
# ==============================

@router.put(
    "/{thread_id}",
    response_model=ThreadResponse
)
def update_thread(
    thread_id: int,
    payload: ThreadUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ThreadService.update_thread(
        db,
        thread_id,
        payload,
        user.id,
        user
    )


# ==============================
# Delete Thread
# ==============================

@router.delete(
    "/{thread_id}",
    response_model=MessageResponse,
)
def delete_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    ThreadService.delete_thread(
        db,
        thread_id,
        user.id,
        user
    )

    return {"message": "Thread deleted"}
