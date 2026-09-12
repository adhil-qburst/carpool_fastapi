from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.routes.domain.enums import RouteStatus
from app.features.routes.domain.rules import (
    ensure_route_exists,
    ensure_route_owner,
)
from app.features.routes.repositories.route_repo import get_route_repo


def delete_route(
    session: Session,
    *,
    route_id: UUID,
    driver_id: UUID,
    settings: Settings | None = None,
) -> None:
    _ = settings or get_settings()
    repo = get_route_repo()

    try:
        route = repo.get_by_id_for_update(session, route_id, status=RouteStatus.ACTIVE)
        ensure_route_exists(route, route_id=route_id)
        ensure_route_owner(route, driver_id=driver_id)

        repo.soft_delete(session, route)
        session.commit()
    except Exception:
        session.rollback()
        raise
