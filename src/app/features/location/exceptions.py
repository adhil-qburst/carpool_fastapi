from decimal import Decimal
from uuid import UUID

from app.core.exceptions import AppError


class LocationNotFoundError(AppError):
    def __init__(self, location_id: UUID | None = None) -> None:
        self.location_id = location_id
        super().__init__("Location not found.", "LOCATION_NOT_FOUND")


class LocationInactiveError(AppError):
    def __init__(self, location_id: UUID | None = None) -> None:
        self.location_id = location_id
        super().__init__("Location is inactive.", "LOCATION_INACTIVE")


class InvalidCoordinatesError(AppError):
    def __init__(
        self,
        lat: Decimal | float | None = None,
        lng: Decimal | float | None = None,
    ) -> None:
        self.lat = lat
        self.lng = lng
        super().__init__(
            "Invalid coordinates. Latitude must be between -90 and 90, and longitude between -180 and 180.",
            "INVALID_COORDINATES",
        )


class InvalidPaginationError(AppError):
    def __init__(self, limit: int, offset: int) -> None:
        self.limit = limit
        self.offset = offset
        super().__init__(
            "Limit must be greater than 0 and offset must be non-negative.",
            "INVALID_PAGINATION",
        )
