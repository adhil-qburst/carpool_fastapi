from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.trips.domain.rules import ensure_valid_pagination
from app.features.trips.models.trip import Trip
from app.features.trips.repositories.trips import get_trip_repo


def list_driver_trips(
    session: Session,
    *,
    driver_id: UUID,
    limit: int = 20,
    offset: int = 0,
    settings: Settings | None = None,
) -> tuple[list[Trip], int]:
    _ = settings or get_settings()
    ensure_valid_pagination(limit=limit, offset=offset)

    repo = get_trip_repo()
    return repo.list_by_driver(
        session,
        driver_id=driver_id,
        limit=limit,
        offset=offset,
    )
