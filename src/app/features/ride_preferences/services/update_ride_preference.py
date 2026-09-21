from datetime import time
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.ride_preferences.domain.rules import (
    ensure_different_locations,
    ensure_no_duplicate_preference,
    ensure_ride_preference_exists,
    ensure_ride_preference_owner,
    ensure_valid_label,
    ensure_valid_seats_needed,
    normalize_label,
)
from app.features.ride_preferences.models.ride_preference import RidePreference
from app.features.ride_preferences.repositories.ride_preferences import get_ride_preference_repo


def update_ride_preference(
    session: Session,
    ride_preference_id: UUID,
    rider_id: UUID,
    *,
    source_location_id: UUID | None = None,
    destination_location_id: UUID | None = None,
    preferred_departure_time: time | None = None,
    seats_needed: int | None = None,
    is_active: bool | None = None,
    label: str | None = None,
    settings: Settings | None = None,
) -> RidePreference:
    _ = settings or get_settings()
    repo = get_ride_preference_repo()

    try:
        preference = repo.get_by_id_for_update(session, ride_preference_id)
        ensure_ride_preference_exists(preference, preference_id=ride_preference_id)
        ensure_ride_preference_owner(preference, rider_id=rider_id)

        normalized_label: str | None = None
        if label is not None:
            normalized_label = normalize_label(label)
            ensure_valid_label(normalized_label)

        if seats_needed is not None:
            ensure_valid_seats_needed(seats_needed)

        effective_source = (
            source_location_id
            if source_location_id is not None
            else preference.source_location_id
        )
        effective_dest = (
            destination_location_id
            if destination_location_id is not None
            else preference.destination_location_id
        )
        effective_active = (
            is_active
            if is_active is not None
            else preference.is_active
        )
        ensure_different_locations(effective_source, effective_dest)

        if effective_active:
            existing = repo.get_active_by_rider_and_locations(
                session,
                rider_id=rider_id,
                source_location_id=effective_source,
                destination_location_id=effective_dest,
            )
            ensure_no_duplicate_preference(
                existing,
                current_preference_id=preference.id,
            )

        updated_preference = repo.update(
            session,
            preference,
            source_location_id=source_location_id,
            destination_location_id=destination_location_id,
            preferred_departure_time=preferred_departure_time,
            seats_needed=seats_needed,
            is_active=is_active,
            label=normalized_label if label is not None else None,
        )
        session.commit()
        return updated_preference
    except Exception:
        session.rollback()
        raise
