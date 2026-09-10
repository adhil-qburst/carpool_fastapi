from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.vehicles.domain.rules import (
    ensure_registration_number_available,
    normalize_registration_number,
)
from app.features.vehicles.models.vehicle import Vehicle
from app.features.vehicles.repositories.vehicles import get_vehicle_repo
from app.features.vehicles.schemas.create_vehicle import CreateVehicleRequest


def create_vehicle(
    session: Session,
    driver_id: UUID,
    payload: CreateVehicleRequest,
    *,
    settings: Settings | None = None,
) -> Vehicle:
    _ = settings or get_settings()
    repo = get_vehicle_repo()

    normalized_reg = normalize_registration_number(payload.registration_number)

    try:
        existing_vehicle = repo.get_by_registration_number(session, normalized_reg)
        ensure_registration_number_available(existing_vehicle)

        vehicle = repo.create(
            session,
            driver_id=driver_id,
            make=payload.make.strip(),
            model=payload.model.strip(),
            registration_number=normalized_reg,
            total_seats=payload.total_seats,
        )
        session.commit()
        return vehicle
    except Exception:
        session.rollback()
        raise
