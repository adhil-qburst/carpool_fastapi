from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.bookings.domain.enums import BookingStatus
from app.features.bookings.domain.rules import ensure_valid_pagination
from app.features.bookings.models.booking import Booking
from app.features.bookings.repositories.bookings import get_booking_repo


def list_user_bookings(
    session: Session,
    *,
    rider_id: UUID,
    status: BookingStatus | None = None,
    limit: int = 20,
    offset: int = 0,
    settings: Settings | None = None,
) -> tuple[list[Booking], int]:
    _ = settings or get_settings()
    ensure_valid_pagination(limit=limit, offset=offset)

    repo = get_booking_repo()
    return repo.list_by_rider(
        session,
        rider_id=rider_id,
        status=status,
        limit=limit,
        offset=offset,
    )
