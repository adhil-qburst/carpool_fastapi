import uuid

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.features.routes.domain.enums import RouteStatus
from app.features.users.models.user import User


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[RouteStatus] = mapped_column(
        SQLEnum(
            RouteStatus,
            name="route_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=RouteStatus.ACTIVE,
        server_default=RouteStatus.ACTIVE.value,
    )

    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    driver: Mapped["User"] = relationship(foreign_keys=[driver_id])

    route_stops: Mapped[list["RouteStop"]] = relationship(back_populates="route")
