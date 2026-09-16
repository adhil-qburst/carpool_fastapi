from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.features.bookings.domain.enums import BookingStatus
from app.features.bookings.models.booking import Booking
from app.features.routes.models.route_stop import RouteStop


class BookingRepo:
    def create(
        self,
        session: Session,
        *,
        rider_id: UUID,
        trip_id: UUID,
        pickup_stop_id: UUID,
        dropoff_stop_id: UUID,
        seats_booked: int,
        status: BookingStatus = BookingStatus.PENDING,
    ) -> Booking:
        booking = Booking(
            rider_id=rider_id,
            trip_id=trip_id,
            pickup_stop_id=pickup_stop_id,
            dropoff_stop_id=dropoff_stop_id,
            seats_booked=seats_booked,
            status=status,
        )
        session.add(booking)
        session.flush()
        return booking

    def get_by_id(self, session: Session, booking_id: UUID) -> Booking | None:
        return session.get(Booking, booking_id)

    def get_by_id_for_update(
        self,
        session: Session,
        booking_id: UUID,
    ) -> Booking | None:
        return session.scalar(
            select(Booking).where(Booking.id == booking_id).with_for_update()
        )

    def get_by_id_with_details(
        self,
        session: Session,
        booking_id: UUID,
    ) -> Booking | None:
        return session.scalar(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                joinedload(Booking.rider),
                joinedload(Booking.trip),
                joinedload(Booking.pickup_stop).joinedload(RouteStop.location),
                joinedload(Booking.dropoff_stop).joinedload(RouteStop.location),
            )
        )

    def list_by_rider(
        self,
        session: Session,
        *,
        rider_id: UUID,
        status: BookingStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Booking], int]:
        stmt = select(Booking).where(Booking.rider_id == rider_id)
        count_stmt = select(func.count(Booking.id)).where(Booking.rider_id == rider_id)

        if status is not None:
            stmt = stmt.where(Booking.status == status)
            count_stmt = count_stmt.where(Booking.status == status)

        total = session.scalar(count_stmt) or 0
        items = list(
            session.scalars(
                stmt.options(
                    joinedload(Booking.trip),
                    joinedload(Booking.pickup_stop).joinedload(RouteStop.location),
                    joinedload(Booking.dropoff_stop).joinedload(RouteStop.location),
                )
                .order_by(Booking.created_at.desc())
                .offset(offset)
                .limit(limit)
            ).unique().all()
        )
        return items, total

    def list_by_trip(
        self,
        session: Session,
        *,
        trip_id: UUID,
        status: BookingStatus | None = None,
    ) -> list[Booking]:
        stmt = select(Booking).where(Booking.trip_id == trip_id)
        if status is not None:
            stmt = stmt.where(Booking.status == status)
        return list(
            session.scalars(
                stmt.options(
                    joinedload(Booking.rider),
                    joinedload(Booking.pickup_stop).joinedload(RouteStop.location),
                    joinedload(Booking.dropoff_stop).joinedload(RouteStop.location),
                ).order_by(Booking.created_at.desc())
            ).unique().all()
        )

    def list_pending_before(
        self,
        session: Session,
        *,
        cutoff: datetime,
    ) -> list[Booking]:
        return list(
            session.scalars(
                select(Booking).where(
                    Booking.status == BookingStatus.PENDING,
                    Booking.created_at <= cutoff,
                )
            ).all()
        )

    def update(
        self,
        session: Session,
        booking: Booking,
        *,
        status: BookingStatus | None = None,
        seats_booked: int | None = None,
    ) -> Booking:
        if status is not None:
            booking.status = status
        if seats_booked is not None:
            booking.seats_booked = seats_booked
        session.flush()
        return booking


def get_booking_repo() -> BookingRepo:
    return BookingRepo()
