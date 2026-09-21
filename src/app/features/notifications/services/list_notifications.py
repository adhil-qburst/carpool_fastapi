from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.notifications.domain.enums import (
    NotificationStatus,
    NotificationType,
)
from app.features.notifications.domain.rules import ensure_valid_pagination
from app.features.notifications.models.notification import Notification
from app.features.notifications.repositories.notifications import get_notification_repo


def list_user_notifications(
    session: Session,
    *,
    user_id: UUID,
    is_read: bool | None = None,
    status: NotificationStatus | None = None,
    type: NotificationType | None = None,
    limit: int = 20,
    offset: int = 0,
    settings: Settings | None = None,
) -> tuple[list[Notification], int, int]:
    _ = settings or get_settings()
    ensure_valid_pagination(limit=limit, offset=offset)

    repo = get_notification_repo()
    items, total = repo.list_by_user(
        session,
        user_id=user_id,
        is_read=is_read,
        status=status,
        type=type,
        limit=limit,
        offset=offset,
    )
    unread_count = repo.get_unread_count(session, user_id=user_id)
    return items, total, unread_count
