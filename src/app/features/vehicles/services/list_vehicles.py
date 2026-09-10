from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.vehicles.models.vehicle import Vehicle
from app.features.vehicles.repositories.vehicles import get_vehicle_repo


def list_user_vehicles(
    session: Session,
    driver_id: UUID,
    *,
    settings: Settings | None = None,
) -> list[Vehicle]:
    _ = settings or get_settings()
    repo = get_vehicle_repo()

    return repo.list_by_driver_id(session, driver_id=driver_id)
