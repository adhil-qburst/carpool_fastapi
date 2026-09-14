from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.trips.domain.rules import (
    ensure_trip_can_be_deleted,
    ensure_trip_exists,
    ensure_trip_ownership,
)
from app.features.trips.repositories.trips import get_trip_repo


def delete_trip(
    session: Session,
    *,
    trip_id: UUID,
    driver_id: UUID,
    settings: Settings | None = None,
) -> None:
    _ = settings or get_settings()
    repo = get_trip_repo()

    try:
        trip = repo.get_by_id_for_update(session, trip_id)
        ensure_trip_exists(trip, trip_id=trip_id)
        ensure_trip_ownership(
            trip.driver_id, current_user_id=driver_id, trip_id=trip_id
        )
        ensure_trip_can_be_deleted(trip.status)

        repo.delete(session, trip)
        session.commit()
    except Exception:
        session.rollback()
        raise
