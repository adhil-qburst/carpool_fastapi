from uuid import UUID

from app.core.exceptions import AppError


class VehicleNotFoundError(AppError):
    def __init__(self, vehicle_id: UUID | None = None) -> None:
        self.vehicle_id = vehicle_id
        super().__init__("Vehicle not found.", "VEHICLE_NOT_FOUND")


class VehicleForbiddenError(AppError):
    def __init__(
        self, vehicle_id: UUID | None = None, user_id: UUID | None = None
    ) -> None:
        self.vehicle_id = vehicle_id
        self.user_id = user_id
        super().__init__(
            "You do not have permission to access or modify this vehicle.",
            "VEHICLE_ACCESS_DENIED",
        )


class VehicleRegistrationAlreadyExistsError(AppError):
    def __init__(self, registration_number: str) -> None:
        self.registration_number = registration_number
        super().__init__(
            f"A vehicle with registration number '{registration_number}' already exists.",
            "VEHICLE_REGISTRATION_ALREADY_EXISTS",
        )
