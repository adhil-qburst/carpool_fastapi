from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.trips.domain.enums import TripStatus
from app.features.trips.domain.rules import (
    ensure_distinct_source_and_destination,
    ensure_valid_pagination,
)
from app.features.trips.models.trip import Trip
from app.features.trips.repositories.trips import get_trip_repo


def search_trips(
    session: Session,
    *,
    source_location_id: UUID,
    destination_location_id: UUID,
    departure_date: date | None = None,
    seats_needed: int | None = None,
    status: TripStatus | None = TripStatus.SCHEDULED,
    limit: int = 20,
    offset: int = 0,
    settings: Settings | None = None,
) -> tuple[list[Trip], int]:
    _ = settings or get_settings()
    ensure_distinct_source_and_destination(
        source_location_id=source_location_id,
        destination_location_id=destination_location_id,
    )
    ensure_valid_pagination(limit=limit, offset=offset)

    repo = get_trip_repo()
    return repo.search(
        session,
        source_location_id=source_location_id,
        destination_location_id=destination_location_id,
        departure_date=departure_date,
        seats_needed=seats_needed,
        status=status,
        limit=limit,
        offset=offset,
    )
