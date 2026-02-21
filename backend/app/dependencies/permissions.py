from fastapi import Depends, HTTPException

from app.dependencies.auth import (
    get_current_user
)
from app.core.constants import Roles
from app.models.user import User


def _has_role(user: User, role_name: str) -> bool:
    return any(
        role.role_name == role_name
        for role in user.roles
    )


def require_admin(user: User = Depends(get_current_user)):

    if not _has_role(user, Roles.ADMIN):
        raise HTTPException(403, "Admin required")

    return user


def require_moderator(
    user: User = Depends(get_current_user)
):

    if not (
        _has_role(user, Roles.ADMIN)
        or _has_role(user, Roles.MODERATOR)
    ):
        raise HTTPException(403, "Moderator required")

    return user
