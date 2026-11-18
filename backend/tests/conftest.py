
from contextlib import ExitStack
from uuid import uuid4

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.dependencies import get_db
from app.main import app
from app.models import Incident, User  # noqa: F401
from app.services.auth import hash_password
from app.services.jwt import create_access_token


@pytest.fixture
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    session = Session(bind=test_engine)

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def anonymous_client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def client_factory(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    stack = ExitStack()

    def create_client(role: str, email: str | None = None):
        if role not in {"ADMIN", "ANALYST", "REVIEWER"}:
            raise ValueError("Invalid test user role.")

        user = User(
            email=email or f"{role.lower()}-{uuid4().hex}@test.local",
            password_hash=hash_password(
                "Temporary-Test-Password-123!"
            ),
            role=role,
            is_active=True,
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = create_access_token(user.id)

        return stack.enter_context(
            TestClient(
                app,
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )
        )

    try:
        yield create_client
    finally:
        stack.close()
        app.dependency_overrides.clear()


@pytest.fixture
def admin_client(client_factory):
    return client_factory("ADMIN")


@pytest.fixture
def analyst_client(client_factory):
    return client_factory("ANALYST")


@pytest.fixture
def reviewer_client(client_factory):
    return client_factory("REVIEWER")


@pytest.fixture
def client(analyst_client):
    return analyst_client
