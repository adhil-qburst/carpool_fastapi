from datetime import date, time
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.trips.domain.enums import TripStatus
from app.features.trips.models.trip import Trip


class TripRepo:
    def create(
        self,
        session: Session,
        *,
        route_id: UUID,
        driver_id: UUID,
        vehicle_id: UUID,
        departure_date: date,
        departure_time: time,
        available_seats: int,
        status: TripStatus = TripStatus.SCHEDULED,
    ) -> Trip:
        trip = Trip(
            route_id=route_id,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            departure_date=departure_date,
            departure_time=departure_time,
            available_seats=available_seats,
            status=status,
        )
        session.add(trip)
        session.flush()
        return trip

    def get_by_id(self, session: Session, trip_id: UUID) -> Trip | None:
        return session.get(Trip, trip_id)

    def get_by_id_for_update(
        self,
        session: Session,
        trip_id: UUID,
    ) -> Trip | None:
        return session.scalar(
            select(Trip).where(Trip.id == trip_id).with_for_update()
        )

    def list_by_driver(
        self,
        session: Session,
        *,
        driver_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Trip], int]:
        total = (
            session.scalar(
                select(func.count())
                .select_from(Trip)
                .where(Trip.driver_id == driver_id)
            )
            or 0
        )
        query = (
            select(Trip)
            .where(Trip.driver_id == driver_id)
            .order_by(Trip.departure_date.asc(), Trip.departure_time.asc())
            .offset(offset)
            .limit(limit)
        )
        items = list(session.scalars(query).all())
        return items, total

    def update(
        self,
        session: Session,
        trip: Trip,
        *,
        vehicle_id: UUID | None = None,
        departure_date: date | None = None,
        departure_time: time | None = None,
        available_seats: int | None = None,
        status: TripStatus | None = None,
    ) -> Trip:
        if vehicle_id is not None:
            trip.vehicle_id = vehicle_id
        if departure_date is not None:
            trip.departure_date = departure_date
        if departure_time is not None:
            trip.departure_time = departure_time
        if available_seats is not None:
            trip.available_seats = available_seats
        if status is not None:
            trip.status = status
        session.flush()
        return trip


    def delete(self, session: Session, trip: Trip) -> None:
        trip.status = TripStatus.DELETED
        session.flush()



def get_trip_repo() -> TripRepo:
    return TripRepo()
