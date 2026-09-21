from datetime import time
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.ride_preferences.domain.rules import (
    ensure_different_locations,
    ensure_no_duplicate_preference,
    ensure_valid_label,
    ensure_valid_seats_needed,
    normalize_label,
)
from app.features.ride_preferences.models.ride_preference import RidePreference
from app.features.ride_preferences.repositories.ride_preferences import get_ride_preference_repo


def create_ride_preference(
    session: Session,
    *,
    rider_id: UUID,
    source_location_id: UUID,
    destination_location_id: UUID,
    preferred_departure_time: time | None = None,
    seats_needed: int = 1,
    is_active: bool = True,
    label: str | None = None,
    settings: Settings | None = None,
) -> RidePreference:
    _ = settings or get_settings()
    repo = get_ride_preference_repo()

    cleaned_label = normalize_label(label)
    ensure_valid_label(cleaned_label)
    ensure_different_locations(source_location_id, destination_location_id)
    ensure_valid_seats_needed(seats_needed)

    try:
        if is_active:
            existing = repo.get_active_by_rider_and_locations(
                session,
                rider_id=rider_id,
                source_location_id=source_location_id,
                destination_location_id=destination_location_id,
            )
            ensure_no_duplicate_preference(existing)

        preference = repo.create(
            session,
            rider_id=rider_id,
            source_location_id=source_location_id,
            destination_location_id=destination_location_id,
            preferred_departure_time=preferred_departure_time,
            seats_needed=seats_needed,
            is_active=is_active,
            label=cleaned_label,
        )
        session.commit()
        return preference
    except Exception:
        session.rollback()
        raise
