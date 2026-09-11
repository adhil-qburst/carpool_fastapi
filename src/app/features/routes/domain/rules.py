from uuid import UUID

from app.features.routes.exceptions import (
    CannotSwapSameStopError,
    DuplicateStopLocationError,
    IdenticalSourceDestinationError,
    InvalidStopSequenceError,
    RouteForbiddenError,
    RouteNameAlreadyExistsError,
    RouteNotFoundError,
    RouteStopNotFoundError,
    StopsDoNotBelongToSameRouteError,
)
from app.features.routes.models.route import Route
from app.features.routes.models.route_stop import RouteStop


def normalize_route_name(name: str) -> str:
    return name.strip()


def ensure_route_exists(
    route: Route | None,
    route_id: UUID | None = None,
) -> Route:
    if route is None:
        raise RouteNotFoundError(route_id=route_id)
    return route


def ensure_route_owner(route: Route, driver_id: UUID) -> None:
    if route.driver_id != driver_id:
        raise RouteForbiddenError(route_id=route.id, user_id=driver_id)


def ensure_route_name_available(
    existing_route: Route | None,
    name: str,
    driver_id: UUID | None = None,
) -> None:
    if existing_route is not None:
        raise RouteNameAlreadyExistsError(name=name, driver_id=driver_id)


def ensure_distinct_source_and_destination(
    source_id: UUID,
    dest_id: UUID,
) -> None:
    if source_id == dest_id:
        raise IdenticalSourceDestinationError(location_id=source_id)


def ensure_stop_exists(
    stop: RouteStop | None,
    stop_id: UUID | None = None,
) -> RouteStop:
    if stop is None:
        raise RouteStopNotFoundError(stop_id=stop_id)
    return stop


def ensure_location_not_in_route(
    existing_stops: list[RouteStop],
    location_id: UUID,
    route_id: UUID | None = None,
) -> None:
    for stop in existing_stops:
        if stop.location_id == location_id:
            raise DuplicateStopLocationError(
                location_id=location_id,
                route_id=route_id,
            )


def ensure_valid_sequence(sequence: int, max_allowed: int) -> None:
    if sequence < 0 or sequence > max_allowed:
        raise InvalidStopSequenceError(sequence=sequence)


def ensure_stops_are_different(stop_id_1: UUID, stop_id_2: UUID) -> None:
    if stop_id_1 == stop_id_2:
        raise CannotSwapSameStopError(stop_id=stop_id_1)


def ensure_stops_belong_to_same_route(
    stop_1: RouteStop,
    stop_2: RouteStop,
) -> None:
    if stop_1.route_id != stop_2.route_id:
        raise StopsDoNotBelongToSameRouteError(
            stop_1_id=stop_1.id,
            stop_2_id=stop_2.id,
        )
