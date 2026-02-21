from sqlalchemy import Column, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import BaseModel


# ==============================
# Junction Table: user_roles
# ==============================

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)


# ==============================
# Role Model
# ==============================

class Role(BaseModel):
    """
    Role model for RBAC.

    Supports:
    - ADMIN
    - MODERATOR
    - MEMBER
    """

    __tablename__ = "roles"

    role_name = Column(String(50), unique=True, nullable=False)

    # Relationships

    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
    )
