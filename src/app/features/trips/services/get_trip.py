from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.trips.domain.rules import (
    ensure_trip_exists,
    ensure_trip_ownership,
)
from app.features.trips.models.trip import Trip
from app.features.trips.repositories.trips import get_trip_repo


def get_trip(
    session: Session,
    *,
    trip_id: UUID,
    driver_id: UUID | None = None,
    settings: Settings | None = None,
) -> Trip:
    _ = settings or get_settings()
    repo = get_trip_repo()

    trip = repo.get_by_id(session, trip_id)
    ensure_trip_exists(trip, trip_id=trip_id)

    if driver_id is not None:
        ensure_trip_ownership(
            trip.driver_id, current_user_id=driver_id, trip_id=trip_id
        )

    return trip
