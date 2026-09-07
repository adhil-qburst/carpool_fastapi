from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.bookings.enums import BookingStatus
from app.models.route_stop import RouteStop
from app.models.trip import Trip
from app.models.user import User


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    pickup_stop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("route_stops.id", ondelete="CASCADE"),
        nullable=False,
    )

    dropoff_stop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("route_stops.id", ondelete="CASCADE"),
        nullable=False,
    )

    seats_booked: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, name="booking_status"),
        nullable=False,
        default=BookingStatus.PENDING,
    )

    trip: Mapped[Trip] = relationship()
    rider: Mapped[User] = relationship()
    pickup_stop: Mapped[RouteStop] = relationship(foreign_keys=[pickup_stop_id])
    dropoff_stop: Mapped[RouteStop] = relationship(foreign_keys=[dropoff_stop_id])

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
