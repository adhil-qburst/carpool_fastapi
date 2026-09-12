from decimal import Decimal
from uuid import UUID

from app.features.location.domain.enums import LocationStatus
from app.features.location.exceptions import (
    InvalidCoordinatesError,
    InvalidPaginationError,
    LocationInactiveError,
    LocationNotFoundError,
)
from app.features.location.models.location import Location


def normalize_location_name(name: str) -> str:
    return name.strip()


def normalize_city_name(city: str) -> str:
    return city.strip()


def ensure_location_exists(
    location: Location | None,
    location_id: UUID | None = None,
) -> Location:
    if location is None:
        raise LocationNotFoundError(location_id=location_id)
    return location


def ensure_location_active(location: Location) -> None:
    if location.status != LocationStatus.ACTIVE:
        raise LocationInactiveError(location_id=location.id)


def ensure_valid_coordinates(
    lat: Decimal | float | None,
    lng: Decimal | float | None,
) -> None:
    if lat is None and lng is None:
        return

    if lat is None or lng is None:
        raise InvalidCoordinatesError(lat=lat, lng=lng)

    try:
        lat_dec = Decimal(str(lat))
        lng_dec = Decimal(str(lng))
    except Exception:
        raise InvalidCoordinatesError(lat=lat, lng=lng)

    if not (Decimal("-90") <= lat_dec <= Decimal("90")):
        raise InvalidCoordinatesError(lat=lat, lng=lng)

    if not (Decimal("-180") <= lng_dec <= Decimal("180")):
        raise InvalidCoordinatesError(lat=lat, lng=lng)


def ensure_valid_pagination(limit: int, offset: int) -> None:
    if limit <= 0 or offset < 0:
        raise InvalidPaginationError(limit=limit, offset=offset)
