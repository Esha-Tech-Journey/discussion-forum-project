from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
)
from app.schemas.base import MessageResponse
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.dependencies.auth import get_current_user
from app.dependencies.rate_limit import (
    login_rate_limiter
)
from app.models.user import User


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# ==============================
# Register
# ==============================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201
)
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register new user account.
    """

    user = AuthService.register_user(db, payload)
    return user


# ==============================
# Login
# ==============================

@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(login_rate_limiter)]
)
def login_user(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and issue JWT tokens.
    """

    tokens = AuthService.login_user(
        db,
        payload.email,
        payload.password,
    )

    return tokens


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):

    token = AuthService.refresh_access_token(
        db,
        payload.refresh_token
    )

    return {"access_token": token}


@router.post(
    "/change-password",
    response_model=MessageResponse,
)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
):
    return AuthService.change_password(
        db,
        payload.email,
        payload.old_password,
        payload.new_password,
    )


# ==============================
# Get Current User
# ==============================

@router.get(
    "/me",
    response_model=UserResponse
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Get authenticated user profile.
    """

    return current_user


@router.put(
    "/me",
    response_model=UserResponse
)
def update_current_user_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = payload.model_dump(exclude_unset=True)
    allowed_fields = {
        key: value
        for key, value in data.items()
        if key in {"name", "bio", "avatar_url"}
    }
    return UserService.update_profile(
        db,
        current_user.id,
        allowed_fields,
    )
