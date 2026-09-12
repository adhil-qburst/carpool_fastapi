from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.location.domain.enums import LocationStatus
from app.features.location.domain.rules import (
    ensure_location_exists,
    ensure_valid_coordinates,
    normalize_city_name,
    normalize_location_name,
)
from app.features.location.models.location import Location
from app.features.location.repositories.locations import get_location_repo


def update_location(
    session: Session,
    location_id: UUID,
    *,
    name: str | None = None,
    city: str | None = None,
    lat: Decimal | None = None,
    lng: Decimal | None = None,
    status: LocationStatus | None = None,
    settings: Settings | None = None,
) -> Location:
    _ = settings or get_settings()
    repo = get_location_repo()

    try:
        location = repo.get_by_id_for_update(session, location_id)
        ensure_location_exists(location, location_id=location_id)

        target_lat = lat if lat is not None else location.lat
        target_lng = lng if lng is not None else location.lng
        if lat is not None or lng is not None:
            ensure_valid_coordinates(target_lat, target_lng)

        normalized_name = normalize_location_name(name) if name is not None else None
        normalized_city = normalize_city_name(city) if city is not None else None

        updated_location = repo.update(
            session,
            location,
            name=normalized_name,
            city=normalized_city,
            lat=lat,
            lng=lng,
            status=status,
        )
        session.commit()
        return updated_location
    except Exception:
        session.rollback()
        raise
