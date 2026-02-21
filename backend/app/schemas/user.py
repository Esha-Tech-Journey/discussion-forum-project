from typing import Optional, List

from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas.base import TimestampSchema


# ==============================
# Create / Register
# ==============================

class UserCreate(BaseModel):
    """
    Request schema for user registration.
    """

    email: EmailStr
    password: str
    name: Optional[str] = None


# ==============================
# Update Profile
# ==============================

class UserUpdate(BaseModel):
    """
    Update user profile.
    """

    name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None


class UserRoleUpdate(BaseModel):
    role_name: str


# ==============================
# Role Response
# ==============================

class RoleResponse(BaseModel):
    id: int
    role_name: str

    model_config = ConfigDict(from_attributes=True)


# ==============================
# User Response
# ==============================

class UserResponse(TimestampSchema):
    """
    Public user response schema.
    """

    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    is_active: bool

    roles: List[RoleResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class UserSuggestionResponse(BaseModel):
    id: int
    name: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ActiveMemberStatsResponse(TimestampSchema):
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    roles: List[RoleResponse] = []
    thread_count: int
    received_like_count: int


class ActiveMemberStatsListResponse(BaseModel):
    items: List[ActiveMemberStatsResponse]
    total: int
    page: int
    size: int
    pages: int
