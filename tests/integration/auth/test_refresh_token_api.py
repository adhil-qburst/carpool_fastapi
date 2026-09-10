from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.features.auth.api import auth
from app.features.auth.domain.entities.auth_token import RefreshedToken
from app.features.auth.exceptions import (
    InvalidRefreshTokenError,
    UnVerifiedUserError,
    UserDisabledError,
)
from app.main import app


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# =============================================================================
# Request payload validation (422)
# =============================================================================


@pytest.mark.parametrize(
    "payload",
    [
        {},  # missing field
        {"refresh_token": ""},  # empty string
        {"refresh_token": "   "},  # whitespace only
        {"refresh_token": 12345},  # wrong data type
        {"refresh_token": None},  # null value
    ],
)
def test_refresh_rejects_invalid_payload(payload, client):
    response = client.post("/api/v1/auth/refresh", json=payload)
    assert response.status_code == 422


# =============================================================================
# Successful token refresh (200)
# =============================================================================


def test_refresh_returns_new_access_token_on_success(monkeypatch, client):
    fake_refreshed = RefreshedToken(
        access_token="new-fake-access-token",
        token_type="bearer",
        expires_in=900,
    )

    captured = {}

    def fake_refresh(session, refresh_token):
        captured["session"] = session
        captured["refresh_token"] = refresh_token
        return fake_refreshed

    monkeypatch.setattr(auth, "refresh_access_token", fake_refresh)

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "valid.jwt.token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new-fake-access-token",
        "token_type": "bearer",
        "expires_in": 900,
    }
    assert captured["refresh_token"] == "valid.jwt.token"


# =============================================================================
# Error mappings (401)
# =============================================================================


def test_refresh_maps_invalid_refresh_token_to_401(monkeypatch, client):
    def fake_refresh(session, refresh_token):
        raise InvalidRefreshTokenError()

    monkeypatch.setattr(auth, "refresh_access_token", fake_refresh)

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.jwt.token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired refresh token."}


def test_refresh_maps_user_disabled_to_401(monkeypatch, client):
    def fake_refresh(session, refresh_token):
        raise UserDisabledError()

    monkeypatch.setattr(auth, "refresh_access_token", fake_refresh)

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "token-of-disabled-user"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "User account is disabled."}


def test_refresh_maps_unverified_user_to_401(monkeypatch, client):
    def fake_refresh(session, refresh_token):
        raise UnVerifiedUserError(user_id=uuid4(), email="user@example.com")

    monkeypatch.setattr(auth, "refresh_access_token", fake_refresh)

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "token-of-unverified-user"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Please verify your email before login."}
