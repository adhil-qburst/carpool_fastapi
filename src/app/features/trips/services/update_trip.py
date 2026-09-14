from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.trips.domain.rules import (
    calculate_available_seats,
    ensure_departure_in_future,
    ensure_trip_can_be_updated,
    ensure_trip_exists,
    ensure_trip_ownership,
)
from app.features.trips.models.trip import Trip
from app.features.trips.repositories.trips import get_trip_repo
from app.features.trips.schemas.update_trip import UpdateTripRequest
from app.features.vehicles.domain.rules import (
    ensure_vehicle_exists,
    ensure_vehicle_owner,
)
from app.features.vehicles.repositories.vehicles import get_vehicle_repo


def update_trip(
    session: Session,
    *,
    trip_id: UUID,
    driver_id: UUID,
    payload: UpdateTripRequest,
    settings: Settings | None = None,
) -> Trip:
    _ = settings or get_settings()
    repo = get_trip_repo()

    try:
        trip = repo.get_by_id_for_update(session, trip_id)
        ensure_trip_exists(trip, trip_id=trip_id)
        ensure_trip_ownership(
            trip.driver_id, current_user_id=driver_id, trip_id=trip_id
        )

        if (
            payload.departure_date is not None
            or payload.departure_time is not None
            or payload.vehicle_id is not None
        ):
            ensure_trip_can_be_updated(trip.status)

        vehicle_repo = get_vehicle_repo()
        new_available_seats = None
        if payload.vehicle_id is not None:
            target_vehicle = vehicle_repo.get_by_id(session, payload.vehicle_id)
            ensure_vehicle_exists(target_vehicle, vehicle_id=payload.vehicle_id)
            ensure_vehicle_owner(target_vehicle, driver_id=driver_id)
            new_available_seats = calculate_available_seats(target_vehicle.total_seats)

        if payload.departure_date is not None or payload.departure_time is not None:
            new_date = (
                payload.departure_date
                if payload.departure_date is not None
                else trip.departure_date
            )
            new_time = (
                payload.departure_time
                if payload.departure_time is not None
                else trip.departure_time
            )
            ensure_departure_in_future(new_date, new_time)

        updated_trip = repo.update(
            session,
            trip,
            vehicle_id=payload.vehicle_id,
            departure_date=payload.departure_date,
            departure_time=payload.departure_time,
            available_seats=new_available_seats,
            status=payload.status,
        )
        session.commit()
        return updated_trip
    except Exception:
        session.rollback()
        raise

