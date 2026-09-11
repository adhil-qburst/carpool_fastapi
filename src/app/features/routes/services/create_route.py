from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.routes.domain.rules import (
    ensure_distinct_source_and_destination,
    ensure_route_name_available,
    normalize_route_name,
)
from app.features.routes.models.route import Route
from app.features.routes.repositories.route_repo import get_route_repo
from app.features.routes.repositories.route_stop_repo import get_route_stop_repo


def create_route(
    session: Session,
    *,
    driver_id: UUID,
    name: str,
    source_id: UUID,
    dest_id: UUID,
    settings: Settings | None = None,
) -> Route:
    _ = settings or get_settings()
    route_repo = get_route_repo()
    route_stop_repo = get_route_stop_repo()

    normalized_name = normalize_route_name(name)
    ensure_distinct_source_and_destination(source_id=source_id, dest_id=dest_id)

    try:
        existing_route = route_repo.get_by_driver_and_name(
            session,
            driver_id=driver_id,
            name=normalized_name,
        )
        ensure_route_name_available(
            existing_route,
            name=normalized_name,
            driver_id=driver_id,
        )

        route = route_repo.create(
            session,
            name=normalized_name,
            driver_id=driver_id,
        )

        route_stop_repo.create(
            session,
            route_id=route.id,
            location_id=source_id,
            sequence=0,
        )
        route_stop_repo.create(
            session,
            route_id=route.id,
            location_id=dest_id,
            sequence=1,
        )

        session.commit()
        return route_repo.get_by_id_with_stops(session, route.id) or route
    except Exception:
        session.rollback()
        raise
