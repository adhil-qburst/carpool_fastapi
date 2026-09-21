from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.notifications.domain.rules import (
    ensure_notification_exists,
    ensure_notification_owner,
)
from app.features.notifications.models.notification import Notification
from app.features.notifications.repositories.notifications import get_notification_repo


def get_notification(
    session: Session,
    *,
    notification_id: UUID,
    user_id: UUID,
    settings: Settings | None = None,
) -> Notification:
    _ = settings or get_settings()
    repo = get_notification_repo()
    notification = repo.get_by_id(session, notification_id)
    notification = ensure_notification_exists(
        notification, notification_id=notification_id
    )
    ensure_notification_owner(notification, user_id=user_id)
    return notification
