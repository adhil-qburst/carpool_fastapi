from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.bookings.domain.enums import BookingStatus
from app.features.bookings.domain.rules import (
    ensure_booking_can_be_cancelled,
    ensure_booking_exists,
    ensure_booking_owner,
    ensure_trip_exists,
)
from app.features.bookings.models.booking import Booking
from app.features.bookings.repositories.bookings import get_booking_repo
from app.features.trips.repositories.trips import get_trip_repo


def cancel_booking(
    session: Session,
    *,
    booking_id: UUID,
    rider_id: UUID,
    settings: Settings | None = None,
) -> Booking:
    _ = settings or get_settings()
    booking_repo = get_booking_repo()
    trip_repo = get_trip_repo()

    try:
        booking = booking_repo.get_by_id_for_update(session, booking_id)
        ensure_booking_exists(booking, booking_id=booking_id)
        ensure_booking_owner(booking.rider_id, rider_id=rider_id, booking_id=booking_id)
        ensure_booking_can_be_cancelled(booking.status, booking_id=booking_id)

        trip = trip_repo.get_by_id_for_update(session, booking.trip_id)
        ensure_trip_exists(trip, trip_id=booking.trip_id)

        new_available_seats = trip.available_seats + booking.seats_booked
        trip_repo.update(session, trip, available_seats=new_available_seats)

        booking_repo.update(session, booking, status=BookingStatus.CANCELLED)
        session.commit()
        return booking
    except Exception:
        session.rollback()
        raise

