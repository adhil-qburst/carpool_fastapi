from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.routes.domain.rules import ensure_valid_pagination
from app.features.routes.models.route import Route
from app.features.routes.repositories.route_repo import get_route_repo


def list_user_routes(
    session: Session,
    driver_id: UUID,
    *,
    limit: int = 20,
    offset: int = 0,
    settings: Settings | None = None,
) -> tuple[list[Route], int]:
    _ = settings or get_settings()
    repo = get_route_repo()

    ensure_valid_pagination(limit=limit, offset=offset)

    items = repo.list_by_driver_id(
        session,
        driver_id=driver_id,
        limit=limit,
        offset=offset,
    )
    total = repo.count_by_driver_id(session, driver_id=driver_id)
    return items, total
