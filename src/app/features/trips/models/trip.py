from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Time, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.features.trips.domain.enums import TripStatus

if TYPE_CHECKING:
    from app.features.routes.models.route import Route
    from app.features.users.models.user import User
    from app.features.vehicles.models.vehicle import Vehicle


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    departure_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    departure_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    available_seats: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[TripStatus] = mapped_column(
        SQLEnum(
            TripStatus,
            name="trip_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=TripStatus.SCHEDULED,
        server_default=TripStatus.SCHEDULED.value,
    )

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

    route: Mapped["Route"] = relationship(foreign_keys=[route_id])
    driver: Mapped["User"] = relationship(foreign_keys=[driver_id])
    vehicle: Mapped["Vehicle"] = relationship(foreign_keys=[vehicle_id])

