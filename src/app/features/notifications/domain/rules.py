from uuid import UUID

from app.features.notifications.exceptions import (
    InvalidPaginationError,
    NotificationForbiddenError,
    NotificationNotFoundError,
)
from app.features.notifications.models.notification import Notification


def ensure_notification_exists(
    notification: Notification | None,
    notification_id: UUID | None = None,
) -> Notification:
    """Invariant check: ensure notification exists, raise NotificationNotFoundError if None."""
    if notification is None:
        raise NotificationNotFoundError(notification_id=notification_id)
    return notification


def ensure_notification_owner(
    notification: Notification,
    user_id: UUID,
) -> None:
    """Invariant check: ensure the user owns the notification."""
    if notification.user_id != user_id:
        raise NotificationForbiddenError(
            notification_id=notification.id,
            user_id=user_id,
        )


def ensure_valid_pagination(limit: int, offset: int) -> None:
    """Invariant check: ensure pagination parameters are valid."""
    if limit <= 0 or offset < 0:
        raise InvalidPaginationError(limit=limit, offset=offset)
