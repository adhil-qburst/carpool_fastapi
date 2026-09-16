from datetime import date, datetime, time, timezone
from uuid import UUID

from app.features.trips.domain.enums import TripStatus
from app.features.trips.exceptions import (
    IdenticalSourceDestinationError,
    InvalidAvailableSeatsError,
    InvalidPaginationError,
    PastDepartureError,
    RouteForbiddenError,
    RouteNotActiveError,
    RouteNotFoundError,
    TripCannotBeDeletedError,
    TripCannotBeModifiedError,
    TripForbiddenError,
    TripNotFoundError,
    VehicleSeatsExceededError,
)


def ensure_trip_exists(trip: object | None, trip_id: UUID | None = None) -> None:
    if trip is None:
        raise TripNotFoundError(trip_id=trip_id)


def ensure_route_exists(route: object | None, route_id: UUID | None = None) -> None:
    if route is None:
        raise RouteNotFoundError(route_id=route_id)


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


def ensure_valid_available_seats(seats: int) -> None:
    if seats < 1:
        raise InvalidAvailableSeatsError(seats=seats)


def calculate_available_seats(total_seats: int) -> int:
    available_seats = total_seats - 1
    ensure_valid_available_seats(available_seats)
    return available_seats


def ensure_available_seats_within_capacity(
    available_seats: int, total_seats: int
) -> None:
    if available_seats > total_seats:
        raise VehicleSeatsExceededError(
            requested_seats=available_seats, total_seats=total_seats
        )



def ensure_trip_ownership(
    trip_driver_id: UUID,
    current_user_id: UUID,
    trip_id: UUID | None = None,
) -> None:
    if trip_driver_id != current_user_id:
        raise TripForbiddenError(trip_id=trip_id, user_id=current_user_id)


def ensure_route_ownership(
    route_driver_id: UUID,
    current_user_id: UUID,
    route_id: UUID | None = None,
) -> None:
    if route_driver_id != current_user_id:
        raise RouteForbiddenError(route_id=route_id, user_id=current_user_id)


def ensure_route_active(
    status: str | None,
    route_id: UUID | None = None,
) -> None:
    if status != "active":
        raise RouteNotActiveError(route_id=route_id)


def ensure_trip_can_be_updated(current_status: TripStatus | str) -> None:
    status_str = (
        current_status.value
        if isinstance(current_status, TripStatus)
        else str(current_status)
    )
    if status_str in (
        TripStatus.CANCELLED.value,
        TripStatus.COMPLETED.value,
        TripStatus.DELETED.value,
    ):
        raise TripCannotBeModifiedError(status=status_str)


def ensure_trip_can_be_deleted(current_status: TripStatus | str) -> None:
    status_str = (
        current_status.value
        if isinstance(current_status, TripStatus)
        else str(current_status)
    )
    if status_str in (TripStatus.COMPLETED.value, TripStatus.DELETED.value):
        raise TripCannotBeDeletedError(status=status_str)



def ensure_valid_pagination(limit: int, offset: int) -> None:
    if limit <= 0 or offset < 0:
        raise InvalidPaginationError(limit=limit, offset=offset)


def ensure_distinct_source_and_destination(
    source_location_id: UUID,
    destination_location_id: UUID,
) -> None:
    if source_location_id == destination_location_id:
        raise IdenticalSourceDestinationError(location_id=source_location_id)

