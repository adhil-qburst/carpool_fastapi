from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.users.api import users
from app.features.users.domain.enums import UserRole
from app.features.users.exceptions import UserNotFoundError
from app.main import app

TEST_USER_ID = UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def auth_client():
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# =============================================================================
# GET /api/v1/users/current_user
# =============================================================================


def test_get_current_user_success(auth_client, monkeypatch):
    fake_user = SimpleNamespace(
        id=TEST_USER_ID,
        name="John Doe",
        email="john.doe@example.com",
        roles=[UserRole.DRIVER, UserRole.RIDER],
    )

    captured = {}

    def fake_get_current_user(session, user_id):
        captured["session"] = session
        captured["user_id"] = user_id
        return fake_user

    monkeypatch.setattr(users, "get_current_user", fake_get_current_user)

    response = auth_client.get("/api/v1/users/current_user")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(TEST_USER_ID),
        "name": "John Doe",
        "email": "john.doe@example.com",
        "roles": ["driver", "rider"],
    }
    assert captured["user_id"] == TEST_USER_ID


def test_get_current_user_not_found_returns_404(auth_client, monkeypatch):
    def fake_get_current_user(session, user_id):
        raise UserNotFoundError()

    monkeypatch.setattr(users, "get_current_user", fake_get_current_user)

    response = auth_client.get("/api/v1/users/current_user")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found in the server"}


def test_get_current_user_unauthorized_without_auth_header(client):
    response = client.get("/api/v1/users/current_user")

    assert response.status_code == 401
