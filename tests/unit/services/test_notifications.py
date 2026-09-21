from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

import app.features.notifications.services.get_notification as get_notif_module
import app.features.notifications.services.get_unread_count as get_unread_module
import app.features.notifications.services.list_notifications as list_notif_module
from app.features.notifications.domain.enums import (
    NotificationStatus,
    NotificationType,
)
from app.features.notifications.domain.rules import (
    ensure_notification_exists,
    ensure_notification_owner,
    ensure_valid_pagination,
)
from app.features.notifications.exceptions import (
    InvalidPaginationError,
    NotificationForbiddenError,
    NotificationNotFoundError,
)


class FakeSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def make_fake_notification(
    notification_id: UUID | None = None,
    user_id: UUID | None = None,
    title: str = "Test Title",
    message: str = "Test Message",
    notif_type: NotificationType = NotificationType.SYSTEM,
    status: NotificationStatus = NotificationStatus.UNREAD,
    is_read: bool = False,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=notification_id or uuid4(),
        user_id=user_id or uuid4(),
        title=title,
        message=message,
        type=notif_type,
        status=status,
        is_read=is_read,
        read_at=None,
        data={"foo": "bar"},
        created_at=now,
        updated_at=now,
    )


# =============================================================================
# Domain Rules Unit Tests
# =============================================================================


def test_ensure_notification_exists_success():
    notif = make_fake_notification()
    res = ensure_notification_exists(notif)
    assert res == notif


def test_ensure_notification_exists_raises():
    notif_id = uuid4()
    with pytest.raises(NotificationNotFoundError) as exc_info:
        ensure_notification_exists(None, notification_id=notif_id)
    assert exc_info.value.notification_id == notif_id
    assert exc_info.value.code == "NOTIFICATION_NOT_FOUND"


def test_ensure_notification_owner_success():
    uid = uuid4()
    notif = make_fake_notification(user_id=uid)
    ensure_notification_owner(notif, uid)


def test_ensure_notification_owner_forbidden():
    owner_id = uuid4()
    other_id = uuid4()
    notif = make_fake_notification(user_id=owner_id)
    with pytest.raises(NotificationForbiddenError) as exc_info:
        ensure_notification_owner(notif, other_id)
    assert exc_info.value.code == "NOTIFICATION_ACCESS_DENIED"


def test_ensure_valid_pagination():
    ensure_valid_pagination(limit=10, offset=0)
    with pytest.raises(InvalidPaginationError):
        ensure_valid_pagination(limit=0, offset=0)
    with pytest.raises(InvalidPaginationError):
        ensure_valid_pagination(limit=10, offset=-1)


# =============================================================================
# Service Unit Tests
# =============================================================================


def test_list_user_notifications_success(monkeypatch):
    session = FakeSession()
    user_id = uuid4()
    items = [make_fake_notification(user_id=user_id)]

    class FakeRepo:
        def list_by_user(self, s, *, user_id, is_read, status, type, limit, offset):
            assert user_id == user_id
            return items, 1

        def get_unread_count(self, s, *, user_id):
            return 1

    monkeypatch.setattr(list_notif_module, "get_notification_repo", lambda: FakeRepo())

    returned_items, total, unread_count = list_notif_module.list_user_notifications(
        session,
        user_id=user_id,
        limit=20,
        offset=0,
    )
    assert returned_items == items
    assert total == 1
    assert unread_count == 1


def test_list_user_notifications_invalid_pagination(monkeypatch):
    session = FakeSession()
    user_id = uuid4()

    with pytest.raises(InvalidPaginationError):
        list_notif_module.list_user_notifications(
            session,
            user_id=user_id,
            limit=0,
            offset=0,
        )


def test_get_user_unread_count(monkeypatch):
    session = FakeSession()
    user_id = uuid4()

    class FakeRepo:
        def get_unread_count(self, s, *, user_id):
            return 5

    monkeypatch.setattr(get_unread_module, "get_notification_repo", lambda: FakeRepo())

    count = get_unread_module.get_user_unread_count(session, user_id=user_id)
    assert count == 5


def test_get_notification_success(monkeypatch):
    session = FakeSession()
    user_id = uuid4()
    notif_id = uuid4()
    notif = make_fake_notification(notification_id=notif_id, user_id=user_id)

    class FakeRepo:
        def get_by_id(self, s, nid):
            return notif

    monkeypatch.setattr(get_notif_module, "get_notification_repo", lambda: FakeRepo())

    res = get_notif_module.get_notification(session, notification_id=notif_id, user_id=user_id)
    assert res == notif


def test_get_notification_not_found(monkeypatch):
    session = FakeSession()
    user_id = uuid4()
    notif_id = uuid4()

    class FakeRepo:
        def get_by_id(self, s, nid):
            return None

    monkeypatch.setattr(get_notif_module, "get_notification_repo", lambda: FakeRepo())

    with pytest.raises(NotificationNotFoundError):
        get_notif_module.get_notification(session, notification_id=notif_id, user_id=user_id)


def test_get_notification_forbidden(monkeypatch):
    session = FakeSession()
    owner_id = uuid4()
    other_id = uuid4()
    notif_id = uuid4()
    notif = make_fake_notification(notification_id=notif_id, user_id=owner_id)

    class FakeRepo:
        def get_by_id(self, s, nid):
            return notif

    monkeypatch.setattr(get_notif_module, "get_notification_repo", lambda: FakeRepo())

    with pytest.raises(NotificationForbiddenError):
        get_notif_module.get_notification(session, notification_id=notif_id, user_id=other_id)
