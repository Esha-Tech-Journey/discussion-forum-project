from types import SimpleNamespace

import pytest

from app.core.constants import Roles
from app.models.role import Role
from app.repositories.role import RoleRepository
from app.repositories.user import UserRepository
from app.services.bootstrap_service import BootstrapService


def _ensure_roles(db):
    role_repo = RoleRepository()
    for role_name in (Roles.ADMIN, Roles.MODERATOR, Roles.MEMBER):
        if role_repo.get_by_name(db, role_name) is None:
            db.add(Role(role_name=role_name))
    db.commit()


def test_bootstrap_creates_roles_and_admin(db):
    BootstrapService.ensure_roles_and_admin(db)

    role_repo = RoleRepository()
    user_repo = UserRepository()
    assert role_repo.get_by_name(db, Roles.ADMIN) is not None
    assert role_repo.get_by_name(db, Roles.MODERATOR) is not None
    assert role_repo.get_by_name(db, Roles.MEMBER) is not None
    assert user_repo.get_by_email(db, "admin@discussionforum.com") is not None


def test_bootstrap_renames_legacy_admin_when_target_missing(db):
    _ensure_roles(db)
    role_repo = RoleRepository()
    admin_role = role_repo.get_by_name(db, Roles.ADMIN)
    user_repo = UserRepository()
    user_repo.create_with_roles(
        db,
        {
            "email": BootstrapService._legacy_admin_email,
            "password_hash": "legacy-hash",
            "name": "Legacy",
            "is_active": True,
        },
        [admin_role],
    )

    # Keep focus on migration path; password verification is covered elsewhere.
    from app.services import bootstrap_service as bs
    original_verify = bs.verify_password
    bs.verify_password = lambda *_args, **_kwargs: True
    try:
        BootstrapService.ensure_roles_and_admin(db)
    finally:
        bs.verify_password = original_verify

    assert user_repo.get_by_email(db, BootstrapService._legacy_admin_email) is None
    assert user_repo.get_by_email(db, "admin@discussionforum.com") is not None


def test_bootstrap_handles_legacy_target_conflict_when_delete_fails(db, monkeypatch):
    _ensure_roles(db)
    role_repo = RoleRepository()
    admin_role = role_repo.get_by_name(db, Roles.ADMIN)
    member_role = role_repo.get_by_name(db, Roles.MEMBER)
    user_repo = UserRepository()

    legacy = user_repo.create_with_roles(
        db,
        {
            "email": BootstrapService._legacy_admin_email,
            "password_hash": "legacy-hash",
            "name": "Legacy",
            "is_active": True,
        },
        [admin_role],
    )
    user_repo.create_with_roles(
        db,
        {
            "email": "admin@discussionforum.com",
            "password_hash": "target-hash",
            "name": "Target",
            "is_active": True,
        },
        [admin_role],
    )

    original_delete = db.delete

    def failing_delete(_obj):
        raise RuntimeError("delete error")

    monkeypatch.setattr(db, "delete", failing_delete)
    monkeypatch.setattr(
        "app.services.bootstrap_service.verify_password",
        lambda *_args, **_kwargs: True,
    )
    BootstrapService.ensure_roles_and_admin(db)
    monkeypatch.setattr(db, "delete", original_delete)

    db.refresh(legacy)
    assert legacy.is_active is False
    assert legacy.email.startswith(f"legacy_admin_{legacy.id}@discussionforum.com")
    assert any(role.role_name == member_role.role_name for role in legacy.roles)


def test_bootstrap_updates_existing_admin_state(db, monkeypatch):
    _ensure_roles(db)
    role_repo = RoleRepository()
    admin_role = role_repo.get_by_name(db, Roles.ADMIN)
    member_role = role_repo.get_by_name(db, Roles.MEMBER)
    user_repo = UserRepository()

    admin_user = user_repo.create_with_roles(
        db,
        {
            "email": "admin@discussionforum.com",
            "password_hash": "stale-hash",
            "name": "Old Name",
            "is_active": False,
        },
        [member_role],
    )

    monkeypatch.setattr("app.services.bootstrap_service.verify_password", lambda *_args, **_kwargs: False)
    monkeypatch.setattr("app.services.bootstrap_service.hash_password", lambda _password: "fresh-hash")

    BootstrapService.ensure_roles_and_admin(db)
    db.refresh(admin_user)

    assert admin_user.password_hash == "fresh-hash"
    assert admin_user.name == "Bootstrap Admin"
    assert admin_user.is_active is True
    assert any(role.role_name == admin_role.role_name for role in admin_user.roles)


def test_bootstrap_returns_early_when_admin_role_still_missing(monkeypatch):
    class FakeRoleRepo:
        def get_by_name(self, _db, _role_name):
            return None

    class FakeDB:
        def __init__(self):
            self.added = []
            self.commits = 0

        def add(self, value):
            self.added.append(value)

        def commit(self):
            self.commits += 1

    fake_db = FakeDB()
    monkeypatch.setattr(BootstrapService, "role_repo", FakeRoleRepo())
    monkeypatch.setattr(BootstrapService, "user_repo", SimpleNamespace(get_by_email=lambda *_args, **_kwargs: None))

    BootstrapService.ensure_roles_and_admin(fake_db)
    assert fake_db.commits == 1
    assert len(fake_db.added) >= 1
