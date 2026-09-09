import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import UUID, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.features.location.domain.enums import LocationStatus


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    lat: Mapped[Decimal | None] = mapped_column(
        Numeric,
        nullable=True,
    )

    lng: Mapped[Decimal | None] = mapped_column(
        Numeric,
        nullable=True,
    )

    status: Mapped[LocationStatus] = mapped_column(
        SQLEnum(
            LocationStatus,
            name="location_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=LocationStatus.ACTIVE,
        server_default=LocationStatus.ACTIVE.value,
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
