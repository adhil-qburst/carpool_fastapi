from datetime import date, datetime, time
from uuid import UUID

from app.features.bookings.domain.enums import BookingStatus
from app.features.bookings.exceptions import (
    BookingForbiddenError,
    BookingNotFoundError,
    DriverCannotBookOwnTripError,
    InsufficientSeatsError,
    InvalidBookingSeatsError,
    InvalidPaginationError,
    InvalidStopSequenceError,
    PastDepartureError,
    RouteStopNotFoundError,
    StopNotInTripRouteError,
    TripNotAvailableForBookingError,
    TripNotFoundError,
)
from app.features.trips.domain.enums import TripStatus


def ensure_booking_exists(
    booking: object | None, booking_id: UUID | None = None
) -> None:
    if booking is None:
        raise BookingNotFoundError(booking_id=booking_id)


def ensure_trip_exists(
    trip: object | None, trip_id: UUID | None = None
) -> None:
    if trip is None:
        raise TripNotFoundError(trip_id=trip_id)


def ensure_valid_seats_booked(seats: int) -> None:
    if seats < 1:
        raise InvalidBookingSeatsError(seats=seats)


def ensure_rider_is_not_driver(driver_id: UUID, rider_id: UUID) -> None:
    if driver_id == rider_id:
        raise DriverCannotBookOwnTripError(driver_id=driver_id, rider_id=rider_id)


def ensure_trip_is_bookable(current_status: TripStatus | str) -> None:
    status_str = (
        current_status.value
        if isinstance(current_status, TripStatus)
        else str(current_status)
    )
    if status_str != TripStatus.SCHEDULED.value:
        raise TripNotAvailableForBookingError(status=status_str)


def ensure_departure_in_future(
    departure_date: date,
    departure_time: time,
    now: datetime | None = None,
) -> None:
    departure_dt = datetime.combine(departure_date, departure_time)
    current_time = now if now is not None else datetime.now()
    if current_time.tzinfo is not None and departure_dt.tzinfo is None:
        departure_dt = departure_dt.replace(tzinfo=current_time.tzinfo)
    elif current_time.tzinfo is None and departure_dt.tzinfo is not None:
        current_time = current_time.replace(tzinfo=departure_dt.tzinfo)

    if departure_dt <= current_time:
        raise PastDepartureError()


def ensure_sufficient_seats(available_seats: int, requested_seats: int) -> None:
    if available_seats < requested_seats:
        raise InsufficientSeatsError(
            requested_seats=requested_seats,
            available_seats=available_seats,
        )


def ensure_stop_exists(
    stop: object | None, stop_id: UUID | None = None
) -> None:
    if stop is None:
        raise RouteStopNotFoundError(stop_id=stop_id)


def ensure_stop_belongs_to_route(
    stop_route_id: UUID, route_id: UUID, stop_id: UUID | None = None
) -> None:
    if stop_route_id != route_id:
        raise StopNotInTripRouteError(stop_id=stop_id, route_id=route_id)


def ensure_pickup_before_dropoff(
    pickup_sequence: int, dropoff_sequence: int
) -> None:
    if pickup_sequence >= dropoff_sequence:
        raise InvalidStopSequenceError()


def ensure_booking_owner(
    booking_rider_id: UUID, rider_id: UUID, booking_id: UUID | None = None
) -> None:
    if booking_rider_id != rider_id:
        raise BookingForbiddenError(booking_id=booking_id, user_id=rider_id)


def ensure_valid_pagination(limit: int, offset: int) -> None:
    if limit <= 0 or offset < 0:
        raise InvalidPaginationError(limit=limit, offset=offset)

