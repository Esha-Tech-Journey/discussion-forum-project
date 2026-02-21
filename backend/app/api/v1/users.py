from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.permissions import require_admin
from app.schemas.user import (
    ActiveMemberStatsListResponse,
    UserSuggestionResponse,
    UserListResponse,
    UserResponse,
    UserRoleUpdate,
    UserUpdate,
)
from app.schemas.user_activity import UserActivityResponse
from app.services.user_service import (
    UserService
)
from app.dependencies.auth import (
    get_current_user
)


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_profile(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    return UserService.get_profile(
        db,
        user.id
    )


@router.get(
    "/suggest",
    response_model=list[UserSuggestionResponse],
)
def suggest_users(
    q: str | None = Query(None),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return UserService.suggest_users(
        db,
        q=q,
        limit=limit,
        exclude_user_id=user.id,
    )


@router.get(
    "/{user_id}/activity",
    response_model=UserActivityResponse,
)
def get_user_activity(
    user_id: int,
    limit_threads: int = Query(10, ge=1, le=50),
    limit_comments: int = Query(10, ge=1, le=50),
    limit_likes: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    return UserService.get_user_activity(
        db,
        admin,
        user_id,
        limit_threads=limit_threads,
        limit_comments=limit_comments,
        limit_likes=limit_likes,
    )


@router.get(
    "",
    response_model=UserListResponse,
)
def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None),
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    return UserService.list_users(
        db,
        page=page,
        size=size,
        q=q,
    )


@router.get(
    "/role-stats",
    response_model=ActiveMemberStatsListResponse,
)
def list_users_by_role_with_stats(
    role_name: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None),
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    return UserService.list_users_by_role_with_stats(
        db,
        role_name=role_name,
        page=page,
        size=size,
        q=q,
    )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    return UserService.update_user(
        db,
        admin,
        user_id,
        payload.model_dump(exclude_unset=True),
    )


@router.post(
    "/{user_id}/roles",
    response_model=UserResponse,
)
def set_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    return UserService.set_user_role(
        db,
        admin,
        user_id,
        payload.role_name,
    )
