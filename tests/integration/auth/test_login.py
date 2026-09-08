from uuid import uuid4

import pytest

from app.features.auth.services import send_email_token


@pytest.fixture
def verification_email(monkeypatch):
    captured = {}

    def fake_send_verification_email(to_email, token, *, settings=None):
        captured.update(email=to_email, token=token)

    monkeypatch.setattr(
        send_email_token,
        "send_verification_email",
        fake_send_verification_email,
    )
    return captured


def test_login_before_register_returns_user_not_found(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": f"{uuid4()}@example.com", "password": "a-secure-password"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "User not found with this email."}


def test_login_before_email_verification_returns_verification_error(
    client, verification_email
):
    email = f"{uuid4()}@example.com"
    password = "a-secure-password"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Pending User",
            "email": email,
            "password": password,
            "roles": ["rider"],
        },
    )
    assert register_response.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Please verify your email before login."}
    assert verification_email["email"] == email


def test_login_after_email_verification_returns_tokens(client, verification_email):
    email = f"{uuid4()}@example.com"
    password = "a-secure-password"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Verified User",
            "email": email,
            "password": password,
            "roles": ["driver"],
        },
    )
    assert register_response.status_code == 201

    verify_response = client.get(
        f"/api/v1/auth/verify-email?token={verification_email['token']}",
        follow_redirects=False,
    )
    assert verify_response.status_code == 303

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


def test_login_with_invalid_password_returns_invalid_credentials(
    client, verification_email
):
    email = f"{uuid4()}@example.com"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Verified User",
            "email": email,
            "password": "a-secure-password",
            "roles": ["rider"],
        },
    )
    assert register_response.status_code == 201
    client.get(
        f"/api/v1/auth/verify-email?token={verification_email['token']}",
        follow_redirects=False,
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "the-wrong-password"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid email or password"}
