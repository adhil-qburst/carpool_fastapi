from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.vehicles.models.vehicle import Vehicle


class VehicleRepo:
    def create(
        self,
        session: Session,
        *,
        driver_id: UUID,
        make: str,
        model: str,
        registration_number: str,
        total_seats: int,
    ) -> Vehicle:
        vehicle = Vehicle(
            driver_id=driver_id,
            make=make,
            model=model,
            registration_number=registration_number,
            total_seats=total_seats,
        )
        session.add(vehicle)
        session.flush()
        return vehicle

    def get_by_id(self, session: Session, vehicle_id: UUID) -> Vehicle | None:
        return session.get(Vehicle, vehicle_id)

    def get_by_id_for_update(
        self,
        session: Session,
        vehicle_id: UUID,
    ) -> Vehicle | None:
        return session.scalar(
            select(Vehicle).where(Vehicle.id == vehicle_id).with_for_update()
        )

    def get_by_registration_number(
        self,
        session: Session,
        registration_number: str,
    ) -> Vehicle | None:
        return session.scalar(
            select(Vehicle).where(Vehicle.registration_number == registration_number)
        )

    def list_by_driver_id(
        self,
        session: Session,
        driver_id: UUID,
    ) -> list[Vehicle]:
        return list(
            session.scalars(
                select(Vehicle)
                .where(Vehicle.driver_id == driver_id)
                .order_by(Vehicle.created_at.desc())
            ).all()
        )

    def update(
        self,
        session: Session,
        vehicle: Vehicle,
        *,
        make: str | None = None,
        model: str | None = None,
        registration_number: str | None = None,
        total_seats: int | None = None,
    ) -> Vehicle:
        if make is not None:
            vehicle.make = make
        if model is not None:
            vehicle.model = model
        if registration_number is not None:
            vehicle.registration_number = registration_number
        if total_seats is not None:
            vehicle.total_seats = total_seats
        session.flush()
        return vehicle

    def delete(self, session: Session, vehicle: Vehicle) -> None:
        session.delete(vehicle)
        session.flush()


def get_vehicle_repo() -> VehicleRepo:
    return VehicleRepo()
