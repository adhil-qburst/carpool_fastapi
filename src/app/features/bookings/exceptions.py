from uuid import UUID

from app.core.exceptions import AppError


class BookingNotFoundError(AppError):
    def __init__(self, booking_id: UUID | None = None) -> None:
        self.booking_id = booking_id
        super().__init__("Booking not found.", "BOOKING_NOT_FOUND")


class BookingForbiddenError(AppError):
    def __init__(
        self, booking_id: UUID | None = None, user_id: UUID | None = None
    ) -> None:
        self.booking_id = booking_id
        self.user_id = user_id
        super().__init__(
            "You do not have permission to access or modify this booking.",
            "BOOKING_ACCESS_DENIED",
        )


class TripNotFoundError(AppError):
    def __init__(self, trip_id: UUID | None = None) -> None:
        self.trip_id = trip_id
        super().__init__("Trip not found.", "TRIP_NOT_FOUND")


class TripNotAvailableForBookingError(AppError):
    def __init__(self, status: str | None = None) -> None:
        self.status = status
        detail = (
            f"Trip with status '{status}' is not available for booking."
            if status
            else "Trip is not available for booking."
        )
        super().__init__(detail, "TRIP_NOT_AVAILABLE_FOR_BOOKING")


class DriverCannotBookOwnTripError(AppError):
    def __init__(
        self, driver_id: UUID | None = None, rider_id: UUID | None = None
    ) -> None:
        self.driver_id = driver_id
        self.rider_id = rider_id
        super().__init__(
            "Drivers cannot book seats on their own trip.",
            "DRIVER_CANNOT_BOOK_OWN_TRIP",
        )


class InsufficientSeatsError(AppError):
    def __init__(
        self, requested_seats: int, available_seats: int
    ) -> None:
        self.requested_seats = requested_seats
        self.available_seats = available_seats
        super().__init__(
            f"Requested {requested_seats} seat(s), but only {available_seats} seat(s) are available.",
            "INSUFFICIENT_SEATS",
        )


class InvalidBookingSeatsError(AppError):
    def __init__(self, seats: int | None = None) -> None:
        self.seats = seats
        super().__init__(
            "Seats booked must be at least 1.",
            "INVALID_BOOKING_SEATS",
        )


class RouteStopNotFoundError(AppError):
    def __init__(self, stop_id: UUID | None = None) -> None:
        self.stop_id = stop_id
        super().__init__("Route stop not found.", "ROUTE_STOP_NOT_FOUND")


class StopNotInTripRouteError(AppError):
    def __init__(
        self, stop_id: UUID | None = None, route_id: UUID | None = None
    ) -> None:
        self.stop_id = stop_id
        self.route_id = route_id
        super().__init__(
            "Selected stop does not belong to the trip's route.",
            "STOP_NOT_IN_TRIP_ROUTE",
        )


class InvalidStopSequenceError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Pickup stop must come before dropoff stop on the route.",
            "INVALID_STOP_SEQUENCE",
        )


class PastDepartureError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Cannot book a trip that has already departed.",
            "PAST_DEPARTURE_NOT_ALLOWED",
        )
