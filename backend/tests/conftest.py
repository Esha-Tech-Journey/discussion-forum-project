import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from fastapi import Request
from uuid import uuid4

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.models.role import Role
from app.core.constants import Roles
from app.dependencies.rate_limit import (
    login_rate_limiter,
    comment_rate_limiter,
)
from app.websocket.manager import manager


SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    yield session

    session.close()


@pytest.fixture(scope="function", autouse=True)
def mock_password_hashing(monkeypatch):
    monkeypatch.setattr(
        "app.services.auth_service.hash_password",
        lambda password: f"hashed::{password}"
    )
    monkeypatch.setattr(
        "app.services.auth_service.verify_password",
        lambda plain_password, hashed_password: (
            hashed_password == f"hashed::{plain_password}"
        )
    )


@pytest.fixture(scope="function")
def client(db):
    async def bypass_rate_limiter(request: Request):
        return None

    async def bypass_redis_listener(channel: str):
        return None

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[login_rate_limiter] = bypass_rate_limiter
    app.dependency_overrides[comment_rate_limiter] = bypass_rate_limiter
    manager.listen_to_channel = bypass_redis_listener

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def token(client):
    email = f"test_{uuid4().hex[:8]}@example.com"
    password = "password123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        }
    )
    assert register_response.status_code in (200, 201)

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        }
    )
    assert login_response.status_code == 200

    return login_response.json()["access_token"]


@pytest.fixture(scope="function")
def register_and_login(client):
    def _register_and_login(
        email: str | None = None,
        password: str = "password123",
        name: str | None = None,
    ) -> dict:
        resolved_email = (
            email
            or f"user_{uuid4().hex[:8]}@example.com"
        )
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": resolved_email,
                "password": password,
                "name": name,
            },
        )
        assert register_response.status_code in (200, 201)

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": resolved_email,
                "password": password,
            },
        )
        assert login_response.status_code == 200
        payload = login_response.json()
        return {
            "email": resolved_email,
            "password": password,
            "access_token": payload["access_token"],
            "refresh_token": payload["refresh_token"],
        }

    return _register_and_login


@pytest.fixture(scope="function")
def assign_role(db):
    def _assign_role(email: str, role_name: str) -> User:
        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )
        assert user is not None

        role = (
            db.query(Role)
            .filter(Role.role_name == role_name)
            .first()
        )
        if role is None:
            role = Role(role_name=role_name)
            db.add(role)
            db.commit()
            db.refresh(role)

        if role_name == Roles.MEMBER:
            user.roles = []
        else:
            user.roles = [role]
        db.commit()
        db.refresh(user)
        return user

    return _assign_role
