from uuid import UUID

from app.features.ride_preferences.exceptions import (
    DuplicateRidePreferenceError,
    InvalidPaginationError,
    InvalidRidePreferenceLabelError,
    InvalidSeatsNeededError,
    RidePreferenceForbiddenError,
    RidePreferenceNotFoundError,
    SameLocationRidePreferenceError,
)
from app.features.ride_preferences.models.ride_preference import RidePreference


def normalize_label(label: str | None) -> str | None:
    """Normalize label string, stripping whitespace or returning None if empty."""
    if label is None:
        return None
    trimmed = label.strip()
    return trimmed if trimmed else None


def ensure_valid_label(label: str | None) -> None:
    """Invariant check: ensure label does not exceed maximum length."""
    if label is not None and len(label) > 100:
        raise InvalidRidePreferenceLabelError(label=label)


def ensure_different_locations(
    source_location_id: UUID,
    destination_location_id: UUID,
) -> None:
    """Invariant check: ensure source and destination locations are distinct."""
    if source_location_id == destination_location_id:
        raise SameLocationRidePreferenceError(
            source_location_id=source_location_id,
            destination_location_id=destination_location_id,
        )


def ensure_valid_seats_needed(seats_needed: int) -> None:
    """Invariant check: ensure seats needed is at least 1."""
    if seats_needed < 1:
        raise InvalidSeatsNeededError(seats_needed=seats_needed)


def ensure_ride_preference_exists(
    preference: RidePreference | None,
    preference_id: UUID | None = None,
) -> RidePreference:
    """Invariant check: ensures ride preference exists, raises domain AppError if None."""
    if preference is None:
        raise RidePreferenceNotFoundError(preference_id=preference_id)
    return preference


def ensure_ride_preference_owner(
    preference: RidePreference,
    rider_id: UUID,
) -> None:
    """Invariant check: ensures rider owns the preference before access/mutation."""
    if preference.rider_id != rider_id:
        raise RidePreferenceForbiddenError(
            preference_id=preference.id,
            user_id=rider_id,
        )


def ensure_no_duplicate_preference(
    existing_preference: RidePreference | None,
    current_preference_id: UUID | None = None,
) -> None:
    """Invariant check: uniqueness check for active preference between same locations."""
    if existing_preference is not None:
        if current_preference_id is None or existing_preference.id != current_preference_id:
            raise DuplicateRidePreferenceError(
                source_location_id=existing_preference.source_location_id,
                destination_location_id=existing_preference.destination_location_id,
            )


def ensure_valid_pagination(limit: int, offset: int) -> None:
    """Invariant check: ensure pagination parameters are valid."""
    if limit <= 0 or offset < 0:
        raise InvalidPaginationError(limit=limit, offset=offset)
