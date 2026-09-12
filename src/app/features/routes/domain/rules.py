from uuid import UUID

from app.features.routes.exceptions import (
    CannotSwapSameStopError,
    DuplicateStopLocationError,
    DuplicateStopSequenceError,
    IdenticalSourceDestinationError,
    InvalidPaginationError,
    InvalidStopSequenceError,
    RouteForbiddenError,
    RouteNameAlreadyExistsError,
    RouteNotFoundError,
    RouteStopNotFoundError,
    StopsDoNotBelongToSameRouteError,
)
from app.features.routes.domain.enums import RouteStatus
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


def ensure_route_active(
    route: Route,
    route_id: UUID | None = None,
) -> None:
    if route.status != RouteStatus.ACTIVE:
        raise RouteNotFoundError(route_id=route_id or route.id)


def ensure_route_owner(route: Route, driver_id: UUID) -> None:
    if route.driver_id != driver_id:
        raise RouteForbiddenError(route_id=route.id, user_id=driver_id)


def ensure_route_name_available(
    existing_route: Route | None,
    name: str,
    driver_id: UUID | None = None,
    current_route_id: UUID | None = None,
) -> None:
    if existing_route is not None:
        if current_route_id is not None and existing_route.id == current_route_id:
            return
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


def ensure_unique_route_locations(
    source_id: UUID,
    dest_id: UUID,
    stop_location_ids: list[UUID] | None = None,
) -> None:
    """Validate that source, destination, and all intermediate stops are unique.

    Ensures that source and destination are distinct, neither source nor
    destination appears in the intermediate stops, and no stop location is duplicated.
    """
    ensure_distinct_source_and_destination(source_id=source_id, dest_id=dest_id)
    if not stop_location_ids:
        return

    seen_locations: set[UUID] = {source_id, dest_id}
    for location_id in stop_location_ids:
        if location_id in seen_locations:
            raise DuplicateStopLocationError(location_id=location_id)
        seen_locations.add(location_id)


def ensure_valid_intermediate_sequence(sequence: int, total_stops: int) -> None:
    """Validate a single intermediate stop sequence.

    Route starts at sequence 0 (source) and ends at sequence total_stops + 1 (dest).
    Intermediate stop sequences must be strictly positive and precede destination
    (1 <= sequence <= total_stops).
    """
    if sequence < 1 or sequence > total_stops:
        raise InvalidStopSequenceError(sequence=sequence)


def ensure_valid_intermediate_sequences(
    sequences: list[int],
    total_stops: int | None = None,
) -> None:
    """Validate intermediate stop sequences.

    Checks that all sequences are strictly positive, valid within the route bounds
    (1 <= sequence <= total_stops), and contain no duplicate sequences.
    """
    if not sequences:
        return

    max_allowed = total_stops if total_stops is not None else len(sequences)
    seen: set[int] = set()

    for seq in sequences:
        if seq < 1 or seq > max_allowed:
            raise InvalidStopSequenceError(sequence=seq)
        if seq in seen:
            raise DuplicateStopSequenceError(sequence=seq)
        seen.add(seq)


ensure_valid_intermediate_stop_sequences = ensure_valid_intermediate_sequences


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


def ensure_valid_pagination(limit: int, offset: int) -> None:
    if limit <= 0 or offset < 0:
        raise InvalidPaginationError(limit=limit, offset=offset)
