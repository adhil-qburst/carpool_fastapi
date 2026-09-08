from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.features.auth.api import auth
from app.features.auth.exceptions import (
    EmailDeliveryError,
    InvalidEmailVerificationTokenError,
)
from app.features.users.domain.enums import UserRole
from app.features.users.models.user import User
from app.main import app


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "payload, expected_status",
    [
        # Missing name
        (
            {
                "email": "user@example.com",
                "password": "stringst",
                "roles": ["driver"],
            },
            422,
        ),
        # Invalid email
        (
            {
                "name": "John",
                "email": "invalid-email",
                "password": "stringst",
                "roles": ["driver"],
            },
            422,
        ),
        # Password too short
        (
            {
                "name": "John",
                "email": "user@example.com",
                "password": "123",
                "roles": ["driver"],
            },
            422,
        ),
        # Missing password
        (
            {
                "name": "John",
                "email": "user@example.com",
                "roles": ["driver"],
            },
            422,
        ),
        # Invalid role
        (
            {
                "name": "John",
                "email": "user@example.com",
                "password": "stringst",
                "roles": ["invalid_role"],
            },
            422,
        ),
    ],
)
def test_register_rejects_invalid_payload(payload, expected_status, client):
    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == expected_status


def test_register_returns_success_message_for_valid_payload(monkeypatch, client):
    captured = {}

    def fake_register_user(db, payload):
        captured["payload"] = payload

    monkeypatch.setattr(auth, "register_user", fake_register_user)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": " John Doe ",
            "email": "JOHN.DOE@EXAMPLE.COM",
            "password": "a-secure-password",
            "roles": ["driver", "rider"],
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "message": "Registration successful. Please check your email to verify your account."
    }
    assert captured["payload"].name == "John Doe"
    assert captured["payload"].email == "john.doe@example.com"
    assert captured["payload"].roles == [UserRole.DRIVER, UserRole.RIDER]


def test_register_returns_service_unavailable_when_email_cannot_be_sent(
    monkeypatch, client
):
    def raise_email_delivery_error(db, payload):
        raise EmailDeliveryError()

    monkeypatch.setattr(auth, "register_user", raise_email_delivery_error)

    response = client.post("/api/v1/auth/register", json=_valid_payload())

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Could not send the verification email. Please try again."
    }


def test_verify_email_redirects_after_verifying_token(monkeypatch, client):
    token = "4d0f14da-3c78-4247-8b97-70450dfc3e85"
    captured = {}

    def fake_verify_user_email(db, received_token):
        captured["token"] = received_token

    monkeypatch.setattr(auth, "verify_user_email", fake_verify_user_email)
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: SimpleNamespace(
            email_verification_success_url="http://frontend.test/success"
        ),
    )

    response = client.get(
        f"/api/v1/auth/verify-email?token={token}",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "http://frontend.test/success"
    assert str(captured["token"]) == token


def test_verify_email_rejects_invalid_or_expired_token(monkeypatch, client):
    def raise_invalid_token(db, token):
        raise InvalidEmailVerificationTokenError()

    monkeypatch.setattr(auth, "verify_user_email", raise_invalid_token)

    response = client.get(
        "/api/v1/auth/verify-email?token=4d0f14da-3c78-4247-8b97-70450dfc3e85",
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "The verification link is invalid, expired, or has already been used."
    }


def _valid_payload():
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "password": "a-secure-password",
        "roles": ["driver"],
    }
