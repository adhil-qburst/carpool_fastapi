from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.routes.domain.rules import (
    ensure_location_not_in_route,
    ensure_route_exists,
    ensure_route_owner,
    ensure_valid_sequence,
)
from app.features.routes.models.route_stop import RouteStop
from app.features.routes.repositories.route_repo import get_route_repo
from app.features.routes.repositories.route_stop_repo import get_route_stop_repo


def add_stop(
    session: Session,
    *,
    route_id: UUID,
    location_id: UUID,
    sequence: int | None = None,
    driver_id: UUID | None = None,
    settings: Settings | None = None,
) -> RouteStop:
    _ = settings or get_settings()
    route_repo = get_route_repo()
    route_stop_repo = get_route_stop_repo()

    try:
        route = route_repo.get_by_id(session, route_id)
        ensure_route_exists(route, route_id=route_id)

        if driver_id is not None:
            ensure_route_owner(route, driver_id=driver_id)

        existing_stops = route_stop_repo.list_by_route_id(session, route_id=route_id)
        ensure_location_not_in_route(
            existing_stops,
            location_id=location_id,
            route_id=route_id,
        )

        num_stops = len(existing_stops)
        if sequence is not None:
            ensure_valid_sequence(sequence, max_allowed=num_stops)
            target_sequence = sequence
        else:
            target_sequence = num_stops - 1 if num_stops >= 2 else num_stops

        for stop in existing_stops:
            if stop.sequence >= target_sequence:
                stop.sequence += 1

        session.flush()

        new_stop = route_stop_repo.create(
            session,
            route_id=route_id,
            location_id=location_id,
            sequence=target_sequence,
        )

        session.commit()
        return new_stop
    except Exception:
        session.rollback()
        raise
