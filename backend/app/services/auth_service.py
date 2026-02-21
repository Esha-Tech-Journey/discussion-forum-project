import logging

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from anyio import from_thread

from app.schemas.user import UserCreate
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    is_token_type,
)
from app.core.constants import Roles
from app.repositories.user import UserRepository
from app.repositories.role import RoleRepository
from app.websocket.handlers import broadcast_new_user


class AuthService:
    """
    Handles authentication business logic.
    """
    user_repo = UserRepository()
    role_repo = RoleRepository()
    logger = logging.getLogger(__name__)

    # ==============================
    # Register User
    # ==============================
    @staticmethod
    def register_user(
        db: Session,
        payload: UserCreate
    ):

        # Check duplicate email
        existing_user = AuthService.user_repo.get_by_email(
            db,
            payload.email,
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        hashed_password = hash_password(payload.password)

        user_data = {
            "email": payload.email,
            "password_hash": hashed_password,
            "name": payload.name,
        }

        # Assign default MEMBER role
        member_role = AuthService.role_repo.get_by_name(
            db,
            Roles.MEMBER,
        )

        roles = [member_role] if member_role else []
        user = AuthService.user_repo.create_with_roles(
            db,
            user_data,
            roles,
        )
        try:
            from_thread.run(
                broadcast_new_user,
                user,
            )
        except Exception:
            # Realtime delivery is best-effort.
            AuthService.logger.warning(
                "Failed to broadcast new user event for user_id=%s",
                user.id,
                exc_info=True,
            )

        return user

    # ==============================
    # Login User
    # ==============================
    @staticmethod
    def login_user(
        db: Session,
        email: str,
        password: str
    ):

        user = AuthService.user_repo.get_by_email(
            db,
            email,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        if not verify_password(
            password,
            user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account deactivated by admin",
            )

        # Token payload
        token_data = {
            "sub": str(user.id),
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def change_password(
        db: Session,
        email: str,
        old_password: str,
        new_password: str,
    ):
        user = AuthService.user_repo.get_by_email(
            db,
            email,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account deactivated by admin",
            )

        if not verify_password(
            old_password,
            user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Old password is incorrect",
            )

        if old_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from old password",
            )

        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 6 characters",
            )

        AuthService.user_repo.update(
            db,
            user,
            {"password_hash": hash_password(new_password)},
        )

        return {"message": "Password updated successfully"}

    @classmethod
    def refresh_access_token(
        cls,
        db: Session,
        refresh_token: str
    ):

        payload = decode_token(refresh_token)
        if not is_token_type(payload, "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Valid refresh token required",
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
            )

        user = cls.user_repo.get_by_id(db, int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account deactivated by admin",
            )

        return create_access_token(
            {"sub": user_id}
        )
