from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.notifications.api import notifications
from app.features.notifications.domain.enums import (
    NotificationStatus,
    NotificationType,
)
from app.features.notifications.exceptions import (
    InvalidPaginationError,
    NotificationForbiddenError,
    NotificationNotFoundError,
)
from app.main import app

TEST_USER_ID = UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def auth_client(client):
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    yield client
    app.dependency_overrides.clear()


def make_fake_notification(
    notification_id: UUID | None = None,
    user_id: UUID | None = None,
    title: str = "Ride booked",
    message: str = "Your ride is confirmed",
    notif_type: NotificationType = NotificationType.BOOKING_CONFIRMATION,
    status: NotificationStatus = NotificationStatus.UNREAD,
    is_read: bool = False,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=notification_id or uuid4(),
        user_id=user_id or TEST_USER_ID,
        title=title,
        message=message,
        type=notif_type,
        status=status,
        is_read=is_read,
        read_at=None,
        data={"booking_id": str(uuid4())},
        created_at=now,
        updated_at=now,
    )


# =============================================================================
# GET /api/v1/notifications
# =============================================================================


def test_list_notifications_empty(auth_client, monkeypatch):
    def fake_list(session, *, user_id, is_read, status, type, limit, offset, settings=None):
        return [], 0, 0

    monkeypatch.setattr(notifications, "list_user_notifications", fake_list)

    response = auth_client.get("/api/v1/notifications")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["unread_count"] == 0
    assert data["page"] == 1
    assert data["limit"] == 20


def test_list_notifications_with_items_and_filters(auth_client, monkeypatch):
    fake_item = make_fake_notification()

    def fake_list(session, *, user_id, is_read, status, type, limit, offset, settings=None):
        assert user_id == TEST_USER_ID
        assert is_read is False
        assert status == NotificationStatus.UNREAD
        assert type == NotificationType.BOOKING_CONFIRMATION
        return [fake_item], 1, 1

    monkeypatch.setattr(notifications, "list_user_notifications", fake_list)

    response = auth_client.get(
        "/api/v1/notifications?is_read=false&status=unread&type=booking_confirmation&page=1&limit=10"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(fake_item.id)
    assert data["items"][0]["title"] == fake_item.title
    assert data["items"][0]["type"] == "booking_confirmation"
    assert data["items"][0]["status"] == "unread"
    assert data["total"] == 1
    assert data["unread_count"] == 1


def test_list_notifications_invalid_pagination(auth_client, monkeypatch):
    def fake_list(session, *, user_id, is_read, status, type, limit, offset, settings=None):
        raise InvalidPaginationError(limit=limit, offset=offset)

    monkeypatch.setattr(notifications, "list_user_notifications", fake_list)

    response = auth_client.get("/api/v1/notifications?page=1&limit=20")
    assert response.status_code == 400
    assert "Limit must be greater than 0" in response.json()["detail"]


# =============================================================================
# GET /api/v1/notifications/unread-count
# =============================================================================


def test_get_unread_count(auth_client, monkeypatch):
    def fake_count(session, *, user_id, settings=None):
        assert user_id == TEST_USER_ID
        return 4

    monkeypatch.setattr(notifications, "get_user_unread_count", fake_count)

    response = auth_client.get("/api/v1/notifications/unread-count")
    assert response.status_code == 200
    assert response.json() == {"unread_count": 4}


# =============================================================================
# GET /api/v1/notifications/{notification_id}
# =============================================================================


def test_get_notification_success(auth_client, monkeypatch):
    notif_id = uuid4()
    fake_item = make_fake_notification(notification_id=notif_id)

    def fake_get(session, *, notification_id, user_id, settings=None):
        assert notification_id == notif_id
        assert user_id == TEST_USER_ID
        return fake_item

    monkeypatch.setattr(notifications, "get_notification", fake_get)

    response = auth_client.get(f"/api/v1/notifications/{notif_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(notif_id)
    assert data["title"] == fake_item.title


def test_get_notification_not_found(auth_client, monkeypatch):
    notif_id = uuid4()

    def fake_get(session, *, notification_id, user_id, settings=None):
        raise NotificationNotFoundError(notification_id=notification_id)

    monkeypatch.setattr(notifications, "get_notification", fake_get)

    response = auth_client.get(f"/api/v1/notifications/{notif_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found."


def test_get_notification_forbidden(auth_client, monkeypatch):
    notif_id = uuid4()

    def fake_get(session, *, notification_id, user_id, settings=None):
        raise NotificationForbiddenError(notification_id=notification_id, user_id=user_id)

    monkeypatch.setattr(notifications, "get_notification", fake_get)

    response = auth_client.get(f"/api/v1/notifications/{notif_id}")
    assert response.status_code == 403
    assert "You do not have permission" in response.json()["detail"]


# =============================================================================
# Unauthorized checks
# =============================================================================


def test_notifications_unauthorized(client):
    res_list = client.get("/api/v1/notifications")
    assert res_list.status_code == 401

    res_unread = client.get("/api/v1/notifications/unread-count")
    assert res_unread.status_code == 401

    res_item = client.get(f"/api/v1/notifications/{uuid4()}")
    assert res_item.status_code == 401
