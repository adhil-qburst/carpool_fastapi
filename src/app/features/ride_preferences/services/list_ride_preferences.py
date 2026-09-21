from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.ride_preferences.domain.rules import ensure_different_locations
from app.features.ride_preferences.models.ride_preference import RidePreference
from app.features.ride_preferences.repositories.ride_preferences import get_ride_preference_repo


def list_user_ride_preferences(
    session: Session,
    rider_id: UUID,
    *,
    active_only: bool = False,
    settings: Settings | None = None,
) -> list[RidePreference]:
    _ = settings or get_settings()
    repo = get_ride_preference_repo()

    return repo.list_by_rider_id(session, rider_id=rider_id, active_only=active_only)


def list_active_preferences_by_locations(
    session: Session,
    *,
    source_location_id: UUID,
    destination_location_id: UUID,
    settings: Settings | None = None,
) -> list[RidePreference]:
    _ = settings or get_settings()
    repo = get_ride_preference_repo()

    ensure_different_locations(source_location_id, destination_location_id)

    return repo.list_active_by_locations(
        session,
        source_location_id=source_location_id,
        destination_location_id=destination_location_id,
    )
