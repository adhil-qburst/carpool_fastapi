from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.bookings.domain.enums import BookingStatus
from app.features.bookings.repositories.bookings import get_booking_repo
from app.features.routes.schemas.route_response import RouteStopResponse
from app.features.trips.domain.rules import (
    ensure_trip_exists,
    ensure_trip_ownership,
)
from app.features.trips.repositories.trips import get_trip_repo
from app.features.trips.schemas.passenger_response import (
    PassengerResponse,
    PassengerUserResponse,
)


def list_trip_passengers(
    session: Session,
    *,
    trip_id: UUID,
    driver_id: UUID,
    status: BookingStatus | None = None,
    settings: Settings | None = None,
) -> list[PassengerResponse]:
    _ = settings or get_settings()
    trip_repo = get_trip_repo()
    booking_repo = get_booking_repo()

    trip = trip_repo.get_by_id(session, trip_id)
    ensure_trip_exists(trip, trip_id=trip_id)
    ensure_trip_ownership(
        trip.driver_id, current_user_id=driver_id, trip_id=trip_id
    )

    bookings = booking_repo.list_by_trip(session, trip_id=trip_id, status=status)

    passengers: list[PassengerResponse] = []
    for b in bookings:
        rider_user = PassengerUserResponse(
            id=b.rider.id,
            name=b.rider.name,
            email=b.rider.email,
        )
        passengers.append(
            PassengerResponse(
                id=b.id,
                booking_id=b.id,
                rider_id=b.rider_id,
                rider_name=b.rider.name,
                rider_email=b.rider.email,
                rider=rider_user,
                seats_booked=b.seats_booked,
                status=b.status,
                pickup_stop=RouteStopResponse.model_validate(b.pickup_stop),
                dropoff_stop=RouteStopResponse.model_validate(b.dropoff_stop),
                created_at=b.created_at,
                updated_at=b.updated_at,
            )
        )
    return passengers
