from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.bookings.domain.enums import BookingStatus
from app.features.bookings.domain.rules import (
    ensure_departure_in_future,
    ensure_pickup_before_dropoff,
    ensure_rider_is_not_driver,
    ensure_stop_belongs_to_route,
    ensure_stop_exists,
    ensure_sufficient_seats,
    ensure_trip_exists,
    ensure_trip_is_bookable,
    ensure_valid_seats_booked,
)
from app.features.bookings.models.booking import Booking
from app.features.bookings.repositories.bookings import get_booking_repo
from app.features.bookings.schemas.create_booking import CreateBookingRequest
from app.features.routes.repositories.route_stop_repo import get_route_stop_repo
from app.features.trips.repositories.trips import get_trip_repo


def create_booking(
    session: Session,
    *,
    rider_id: UUID,
    payload: CreateBookingRequest,
    settings: Settings | None = None,
) -> Booking:
    _ = settings or get_settings()

    trip_repo = get_trip_repo()
    booking_repo = get_booking_repo()
    route_stop_repo = get_route_stop_repo()

    try:
        trip = trip_repo.get_by_id_for_update(session, payload.trip_id)
        ensure_trip_exists(trip, trip_id=payload.trip_id)
        ensure_rider_is_not_driver(trip.driver_id, rider_id=rider_id)
        ensure_trip_is_bookable(trip.status)
        ensure_departure_in_future(trip.departure_date, trip.departure_time)
        ensure_valid_seats_booked(payload.seats_booked)
        ensure_sufficient_seats(trip.available_seats, payload.seats_booked)

        pickup_stop = route_stop_repo.get_by_id(session, payload.pickup_stop_id)
        ensure_stop_exists(pickup_stop, stop_id=payload.pickup_stop_id)
        ensure_stop_belongs_to_route(
            pickup_stop.route_id, trip.route_id, stop_id=payload.pickup_stop_id
        )

        dropoff_stop = route_stop_repo.get_by_id(session, payload.dropoff_stop_id)
        ensure_stop_exists(dropoff_stop, stop_id=payload.dropoff_stop_id)
        ensure_stop_belongs_to_route(
            dropoff_stop.route_id, trip.route_id, stop_id=payload.dropoff_stop_id
        )

        ensure_pickup_before_dropoff(pickup_stop.sequence, dropoff_stop.sequence)

        new_available_seats = trip.available_seats - payload.seats_booked
        trip_repo.update(session, trip, available_seats=new_available_seats)

        booking = booking_repo.create(
            session,
            rider_id=rider_id,
            trip_id=payload.trip_id,
            pickup_stop_id=payload.pickup_stop_id,
            dropoff_stop_id=payload.dropoff_stop_id,
            seats_booked=payload.seats_booked,
            status=BookingStatus.PENDING,
        )

        session.commit()
        return booking
    except Exception:
        session.rollback()
        raise
