from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.routes.repositories.route_repo import get_route_repo
from app.features.trips.domain.rules import (
    calculate_available_seats,
    ensure_departure_in_future,
    ensure_route_active,
    ensure_route_exists,
    ensure_route_ownership,
)
from app.features.trips.models.trip import Trip
from app.features.trips.repositories.trips import get_trip_repo
from app.features.trips.schemas.create_trip import CreateTripRequest
from app.features.vehicles.domain.rules import (
    ensure_vehicle_exists,
    ensure_vehicle_owner,
)
from app.features.vehicles.repositories.vehicles import get_vehicle_repo
from app.tasks.notification_tasks import process_trip_notification_task


def create_trip(
    session: Session,
    *,
    driver_id: UUID,
    payload: CreateTripRequest,
    settings: Settings | None = None,
) -> Trip:
    _ = settings or get_settings()

    route_repo = get_route_repo()
    route = route_repo.get_by_id(session, payload.route_id)
    ensure_route_exists(route, route_id=payload.route_id)
    ensure_route_ownership(
        route.driver_id, current_user_id=driver_id, route_id=payload.route_id
    )
    status_str = (
        route.status.value if hasattr(route.status, "value") else str(route.status)
    )
    ensure_route_active(status_str, route_id=payload.route_id)

    vehicle_repo = get_vehicle_repo()
    vehicle = vehicle_repo.get_by_id(session, payload.vehicle_id)
    ensure_vehicle_exists(vehicle, vehicle_id=payload.vehicle_id)
    ensure_vehicle_owner(vehicle, driver_id=driver_id)

    ensure_departure_in_future(payload.departure_date, payload.departure_time)
    available_seats = calculate_available_seats(vehicle.total_seats)

    trip_repo = get_trip_repo()
    try:
        trip = trip_repo.create(
            session,
            route_id=payload.route_id,
            driver_id=driver_id,
            vehicle_id=payload.vehicle_id,
            departure_date=payload.departure_date,
            departure_time=payload.departure_time,
            available_seats=available_seats,
        )
        session.commit()
        process_trip_notification_task.send(str(trip.id))
        return trip
    except Exception:
        session.rollback()
        raise

