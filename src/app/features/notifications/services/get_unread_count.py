from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.notifications.repositories.notifications import get_notification_repo


def get_user_unread_count(
    session: Session,
    *,
    user_id: UUID,
    settings: Settings | None = None,
) -> int:
    _ = settings or get_settings()
    repo = get_notification_repo()
    return repo.get_unread_count(session, user_id=user_id)
