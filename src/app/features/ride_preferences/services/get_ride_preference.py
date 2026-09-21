from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.ride_preferences.domain.rules import (
    ensure_ride_preference_exists,
    ensure_ride_preference_owner,
)
from app.features.ride_preferences.models.ride_preference import RidePreference
from app.features.ride_preferences.repositories.ride_preferences import get_ride_preference_repo


def get_ride_preference(
    session: Session,
    ride_preference_id: UUID,
    rider_id: UUID,
    *,
    with_details: bool = True,
    settings: Settings | None = None,
) -> RidePreference:
    _ = settings or get_settings()
    repo = get_ride_preference_repo()

    if with_details:
        preference = repo.get_by_id_with_details(session, ride_preference_id)
    else:
        preference = repo.get_by_id(session, ride_preference_id)

    ensure_ride_preference_exists(preference, preference_id=ride_preference_id)
    ensure_ride_preference_owner(preference, rider_id=rider_id)

    return preference
