from uuid import UUID

from app.features.vehicles.exceptions import (
    VehicleForbiddenError,
    VehicleNotFoundError,
    VehicleRegistrationAlreadyExistsError,
)
from app.features.vehicles.models.vehicle import Vehicle


def normalize_registration_number(registration_number: str) -> str:
    return registration_number.strip().upper()


def ensure_vehicle_exists(vehicle: Vehicle | None, vehicle_id: UUID | None = None) -> Vehicle:
    if vehicle is None:
        raise VehicleNotFoundError(vehicle_id=vehicle_id)
    return vehicle


def ensure_vehicle_owner(vehicle: Vehicle, driver_id: UUID) -> None:
    if vehicle.driver_id != driver_id:
        raise VehicleForbiddenError(vehicle_id=vehicle.id, user_id=driver_id)


def ensure_registration_number_available(
    existing_vehicle: Vehicle | None,
    current_vehicle_id: UUID | None = None,
) -> None:
    if existing_vehicle is not None:
        if current_vehicle_id is None or existing_vehicle.id != current_vehicle_id:
            raise VehicleRegistrationAlreadyExistsError(
                registration_number=existing_vehicle.registration_number
            )
