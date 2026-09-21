from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.ride_preferences.domain.rules import (
    ensure_ride_preference_exists,
    ensure_ride_preference_owner,
)
from app.features.ride_preferences.repositories.ride_preferences import get_ride_preference_repo


def delete_ride_preference(
    session: Session,
    ride_preference_id: UUID,
    rider_id: UUID,
    *,
    settings: Settings | None = None,
) -> None:
    _ = settings or get_settings()
    repo = get_ride_preference_repo()

    try:
        preference = repo.get_by_id_for_update(session, ride_preference_id)
        ensure_ride_preference_exists(preference, preference_id=ride_preference_id)
        ensure_ride_preference_owner(preference, rider_id=rider_id)

        repo.delete(session, preference)
        session.commit()
    except Exception:
        session.rollback()
        raise
