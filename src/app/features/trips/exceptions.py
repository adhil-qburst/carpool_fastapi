from uuid import UUID

from app.core.exceptions import AppError


class TripNotFoundError(AppError):
    def __init__(self, trip_id: UUID | None = None) -> None:
        self.trip_id = trip_id
        super().__init__("Trip not found.", "TRIP_NOT_FOUND")


class TripForbiddenError(AppError):
    def __init__(
        self, trip_id: UUID | None = None, user_id: UUID | None = None
    ) -> None:
        self.trip_id = trip_id
        self.user_id = user_id
        super().__init__(
            "You do not have permission to access or modify this trip.",
            "TRIP_ACCESS_DENIED",
        )


class PastDepartureError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Departure date and time must be in the future.",
            "PAST_DEPARTURE_NOT_ALLOWED",
        )


class InvalidAvailableSeatsError(AppError):
    def __init__(self, seats: int | None = None) -> None:
        self.seats = seats
        super().__init__(
            "Available seats must be greater than zero.",
            "INVALID_AVAILABLE_SEATS",
        )


class VehicleSeatsExceededError(AppError):
    def __init__(self, requested_seats: int, total_seats: int) -> None:
        self.requested_seats = requested_seats
        self.total_seats = total_seats
        super().__init__(
            f"Available seats ({requested_seats}) cannot exceed vehicle capacity ({total_seats}).",
            "VEHICLE_SEATS_EXCEEDED",
        )



class TripCannotBeModifiedError(AppError):
    def __init__(self, status: str | None = None) -> None:
        self.status = status
        detail = (
            f"Trips with status '{status}' cannot be modified."
            if status
            else "Trips that are cancelled or completed cannot be modified."
        )
        super().__init__(detail, "TRIP_CANNOT_BE_MODIFIED")


class TripCannotBeDeletedError(AppError):
    def __init__(self, status: str | None = None) -> None:
        self.status = status
        detail = (
            f"Trips with status '{status}' cannot be deleted."
            if status
            else "Completed trips cannot be deleted."
        )
        super().__init__(detail, "TRIP_CANNOT_BE_DELETED")


class RouteNotActiveError(AppError):
    def __init__(self, route_id: UUID | None = None) -> None:
        self.route_id = route_id
        super().__init__(
            "Cannot schedule a trip for an inactive route.",
            "ROUTE_NOT_ACTIVE",
        )


class RouteForbiddenError(AppError):
    def __init__(
        self, route_id: UUID | None = None, user_id: UUID | None = None
    ) -> None:
        self.route_id = route_id
        self.user_id = user_id
        super().__init__(
            "You do not have permission to schedule a trip on this route.",
            "ROUTE_ACCESS_DENIED",
        )


class RouteNotFoundError(AppError):
    def __init__(self, route_id: UUID | None = None) -> None:
        self.route_id = route_id
        super().__init__("Route not found.", "ROUTE_NOT_FOUND")


class InvalidPaginationError(AppError):
    def __init__(self, limit: int, offset: int) -> None:
        self.limit = limit
        self.offset = offset
        super().__init__(
            "Limit must be greater than 0 and offset must be non-negative.",
            "INVALID_PAGINATION",
        )


class IdenticalSourceDestinationError(AppError):
    def __init__(self, location_id: UUID | None = None) -> None:
        self.location_id = location_id
        super().__init__(
            "Source and destination locations cannot be identical.",
            "IDENTICAL_SOURCE_DESTINATION",
        )

