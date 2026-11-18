from uuid import uuid4

import pytest

from app.models import User
from app.services.auth import hash_password
from app.services.jwt import create_access_token


TEST_PASSWORD = "Temporary-Test-Password-123!"


def create_test_user(
    db_session,
    *,
    email="analyst@example.com",
    password=TEST_PASSWORD,
    role="ANALYST",
    is_active=True,
):
    user = User(
        id=uuid4(),
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_login_with_valid_credentials(client, db_session):
    create_test_user(db_session)

    response = client.post(
        "/api/auth/login",
        json={
            "email": "analyst@example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_login_rejects_incorrect_password(client, db_session):
    create_test_user(db_session)

    response = client.post(
        "/api/auth/login",
        json={
            "email": "analyst@example.com",
            "password": "Wrong-Password-123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_rejects_unknown_email(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "unknown@example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_rejects_disabled_user(client, db_session):
    create_test_user(
        db_session,
        is_active=False,
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "analyst@example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 401


def test_login_normalizes_email(client, db_session):
    create_test_user(db_session)

    response = client.post(
        "/api/auth/login",
        json={
            "email": "  ANALYST@EXAMPLE.COM  ",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200


def test_login_rejects_invalid_email(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "not-an-email",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 422


def test_login_rejects_extra_fields(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "analyst@example.com",
            "password": TEST_PASSWORD,
            "role": "ADMIN",
        },
    )

    assert response.status_code == 422


def test_me_rejects_missing_token(anonymous_client):
    response = anonymous_client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_rejects_invalid_token(anonymous_client):
    response = anonymous_client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401


def test_me_returns_authenticated_user_without_password_hash(
    client,
    db_session,
):
    user = create_test_user(db_session)

    token = create_access_token(user.id)

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(user.id)
    assert data["email"] == user.email
    assert data["role"] == user.role
    assert data["is_active"] is True

    assert "password_hash" not in data
    assert "password" not in data


def test_me_rejects_disabled_user(client, db_session):
    user = create_test_user(
        db_session,
        is_active=False,
    )

    token = create_access_token(user.id)

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"email": "analyst@example.com"},
        {"password": TEST_PASSWORD},
    ],
)
def test_login_rejects_missing_required_fields(client, payload):
    response = client.post(
        "/api/auth/login",
        json=payload,
    )

    assert response.status_code == 422
