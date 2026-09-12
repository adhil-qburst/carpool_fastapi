from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.location.domain.rules import ensure_location_exists
from app.features.location.models.location import Location
from app.features.location.repositories.locations import get_location_repo


def get_location(
    session: Session,
    location_id: UUID,
    *,
    settings: Settings | None = None,
) -> Location:
    _ = settings or get_settings()
    repo = get_location_repo()

    location = repo.get_by_id(session, location_id)
    return ensure_location_exists(location, location_id=location_id)
