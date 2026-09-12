from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.location.domain.enums import LocationStatus
from app.features.location.domain.rules import (
    ensure_valid_coordinates,
    normalize_city_name,
    normalize_location_name,
)
from app.features.location.models.location import Location
from app.features.location.repositories.locations import get_location_repo


def create_location(
    session: Session,
    *,
    name: str,
    city: str,
    lat: Decimal | None = None,
    lng: Decimal | None = None,
    status: LocationStatus = LocationStatus.ACTIVE,
    settings: Settings | None = None,
) -> Location:
    _ = settings or get_settings()
    repo = get_location_repo()

    normalized_name = normalize_location_name(name)
    normalized_city = normalize_city_name(city)
    ensure_valid_coordinates(lat, lng)

    try:
        location = repo.create(
            session,
            name=normalized_name,
            city=normalized_city,
            lat=lat,
            lng=lng,
            status=status,
        )
        session.commit()
        return location
    except Exception:
        session.rollback()
        raise
