from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.vehicles.domain.rules import (
    ensure_vehicle_exists,
    ensure_vehicle_owner,
)
from app.features.vehicles.models.vehicle import Vehicle
from app.features.vehicles.repositories.vehicles import get_vehicle_repo


def get_vehicle(
    session: Session,
    vehicle_id: UUID,
    driver_id: UUID,
    *,
    settings: Settings | None = None,
) -> Vehicle:
    _ = settings or get_settings()
    repo = get_vehicle_repo()

    vehicle = repo.get_by_id(session, vehicle_id)
    ensure_vehicle_exists(vehicle, vehicle_id=vehicle_id)
    ensure_vehicle_owner(vehicle, driver_id=driver_id)

    return vehicle
