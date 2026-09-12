from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.location.domain.enums import LocationStatus
from app.features.location.domain.rules import ensure_valid_pagination
from app.features.location.models.location import Location
from app.features.location.repositories.locations import get_location_repo


def search_locations(
    session: Session,
    *,
    text: str = "",
    limit: int = 20,
    offset: int = 0,
    status: LocationStatus | None = LocationStatus.ACTIVE,
    settings: Settings | None = None,
) -> tuple[list[Location], int]:
    _ = settings or get_settings()
    repo = get_location_repo()

    ensure_valid_pagination(limit=limit, offset=offset)

    cleaned_text = text.strip()
    locations = repo.search(
        session,
        text=cleaned_text,
        limit=limit,
        offset=offset,
        status=status,
    )
    total_count = repo.count_search(
        session,
        text=cleaned_text,
        status=status,
    )

    return locations, total_count
