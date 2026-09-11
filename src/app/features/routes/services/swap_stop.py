from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.routes.domain.rules import (
    ensure_route_exists,
    ensure_route_owner,
    ensure_stop_exists,
    ensure_stops_are_different,
    ensure_stops_belong_to_same_route,
)
from app.features.routes.exceptions import StopsDoNotBelongToSameRouteError
from app.features.routes.models.route_stop import RouteStop
from app.features.routes.repositories.route_repo import get_route_repo
from app.features.routes.repositories.route_stop_repo import get_route_stop_repo


def swap_stop(
    session: Session,
    *,
    stop_id_1: UUID,
    stop_id_2: UUID,
    route_id: UUID | None = None,
    driver_id: UUID | None = None,
    settings: Settings | None = None,
) -> tuple[RouteStop, RouteStop]:
    _ = settings or get_settings()
    route_repo = get_route_repo()
    route_stop_repo = get_route_stop_repo()

    ensure_stops_are_different(stop_id_1, stop_id_2)

    try:
        stop_1 = route_stop_repo.get_by_id_for_update(session, stop_id_1)
        ensure_stop_exists(stop_1, stop_id=stop_id_1)

        stop_2 = route_stop_repo.get_by_id_for_update(session, stop_id_2)
        ensure_stop_exists(stop_2, stop_id=stop_id_2)

        ensure_stops_belong_to_same_route(stop_1, stop_2)

        if route_id is not None and stop_1.route_id != route_id:
            raise StopsDoNotBelongToSameRouteError(
                stop_1_id=stop_id_1,
                stop_2_id=stop_id_2,
            )

        if driver_id is not None:
            route = route_repo.get_by_id(session, stop_1.route_id)
            ensure_route_exists(route, route_id=stop_1.route_id)
            ensure_route_owner(route, driver_id=driver_id)

        stop_1.sequence, stop_2.sequence = stop_2.sequence, stop_1.sequence

        session.flush()
        session.commit()
        return (stop_1, stop_2)
    except Exception:
        session.rollback()
        raise
