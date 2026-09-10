from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.vehicles.domain.rules import (
    ensure_registration_number_available,
    ensure_vehicle_exists,
    ensure_vehicle_owner,
    normalize_registration_number,
)
from app.features.vehicles.models.vehicle import Vehicle
from app.features.vehicles.repositories.vehicles import get_vehicle_repo
from app.features.vehicles.schemas.update_vehicle import UpdateVehicleRequest


def update_vehicle(
    session: Session,
    vehicle_id: UUID,
    driver_id: UUID,
    payload: UpdateVehicleRequest,
    *,
    settings: Settings | None = None,
) -> Vehicle:
    _ = settings or get_settings()
    repo = get_vehicle_repo()

    try:
        vehicle = repo.get_by_id_for_update(session, vehicle_id)
        ensure_vehicle_exists(vehicle, vehicle_id=vehicle_id)
        ensure_vehicle_owner(vehicle, driver_id=driver_id)

        normalized_reg: str | None = None
        if payload.registration_number is not None:
            normalized_reg = normalize_registration_number(payload.registration_number)
            if normalized_reg != vehicle.registration_number:
                existing_vehicle = repo.get_by_registration_number(
                    session, normalized_reg
                )
                ensure_registration_number_available(
                    existing_vehicle,
                    current_vehicle_id=vehicle.id,
                )

        updated_vehicle = repo.update(
            session,
            vehicle,
            make=payload.make.strip() if payload.make is not None else None,
            model=payload.model.strip() if payload.model is not None else None,
            registration_number=normalized_reg,
            total_seats=payload.total_seats,
        )
        session.commit()
        return updated_vehicle
    except Exception:
        session.rollback()
        raise
