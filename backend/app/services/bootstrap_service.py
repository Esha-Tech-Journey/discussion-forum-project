from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import Roles
from app.core.security import hash_password, verify_password
from app.models.role import Role
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository


class BootstrapService:
    role_repo = RoleRepository()
    user_repo = UserRepository()
    _legacy_admin_email = "admin@discussionforum.local"

    @classmethod
    def ensure_roles_and_admin(cls, db: Session) -> None:
        roles = {
            Roles.ADMIN,
            Roles.MODERATOR,
            Roles.MEMBER,
        }
        for role_name in roles:
            role = cls.role_repo.get_by_name(db, role_name)
            if not role:
                db.add(Role(role_name=role_name))
        db.commit()

        admin_role = cls.role_repo.get_by_name(db, Roles.ADMIN)
        if not admin_role:
            return

        legacy_admin = cls.user_repo.get_by_email(
            db,
            cls._legacy_admin_email,
        )
        target_admin = cls.user_repo.get_by_email(
            db,
            settings.BOOTSTRAP_ADMIN_EMAIL,
        )
        if legacy_admin and not target_admin:
            legacy_admin.email = settings.BOOTSTRAP_ADMIN_EMAIL
            db.commit()
            db.refresh(legacy_admin)
        elif (
            legacy_admin
            and target_admin
            and legacy_admin.id != target_admin.id
        ):
            try:
                db.delete(legacy_admin)
                db.commit()
            except Exception:
                db.rollback()
                legacy_admin.is_active = False
                legacy_admin.email = (
                    f"legacy_admin_{legacy_admin.id}@discussionforum.com"
                )
                member_role = cls.role_repo.get_by_name(
                    db,
                    Roles.MEMBER,
                )
                if member_role:
                    legacy_admin.roles = [member_role]
                db.commit()
                db.refresh(legacy_admin)

        admin_user = cls.user_repo.get_by_email(
            db,
            settings.BOOTSTRAP_ADMIN_EMAIL,
        )

        if not admin_user:
            admin_user = cls.user_repo.create_with_roles(
                db,
                {
                    "email": settings.BOOTSTRAP_ADMIN_EMAIL,
                    "password_hash": hash_password(
                        settings.BOOTSTRAP_ADMIN_PASSWORD
                    ),
                    "name": settings.BOOTSTRAP_ADMIN_NAME,
                    "is_active": True,
                },
                [admin_role],
            )
            return

        has_admin = any(
            role.role_name == Roles.ADMIN
            for role in admin_user.roles
        )
        if not has_admin:
            admin_user.roles = [admin_role]
        # Keep bootstrap admin credentials deterministic after DB resets/manual edits.
        if not verify_password(
            settings.BOOTSTRAP_ADMIN_PASSWORD,
            admin_user.password_hash,
        ):
            admin_user.password_hash = hash_password(
                settings.BOOTSTRAP_ADMIN_PASSWORD
            )
        if admin_user.name != settings.BOOTSTRAP_ADMIN_NAME:
            admin_user.name = settings.BOOTSTRAP_ADMIN_NAME
        if not admin_user.is_active:
            admin_user.is_active = True
        db.commit()
        db.refresh(admin_user)
