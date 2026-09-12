from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.location.domain.rules import ensure_location_exists
from app.features.location.repositories.locations import get_location_repo


def delete_location(
    session: Session,
    location_id: UUID,
    *,
    settings: Settings | None = None,
) -> None:
    _ = settings or get_settings()
    repo = get_location_repo()

    try:
        location = repo.get_by_id_for_update(session, location_id)
        ensure_location_exists(location, location_id=location_id)

        repo.delete(session, location)
        session.commit()
    except Exception:
        session.rollback()
        raise
