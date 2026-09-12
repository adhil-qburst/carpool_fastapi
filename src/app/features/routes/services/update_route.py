from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.features.routes.domain.rules import (
    ensure_route_exists,
    ensure_route_name_available,
    ensure_route_owner,
    ensure_unique_route_locations,
    ensure_valid_intermediate_sequences,
    normalize_route_name,
)
from app.features.routes.models.route import Route
from app.features.routes.repositories.route_repo import get_route_repo
from app.features.routes.repositories.route_stop_repo import get_route_stop_repo
from app.features.routes.schemas.create_route import CreateRouteStopRequest


def _extract_stop_location_id(stop: CreateRouteStopRequest | Any) -> UUID:
    if hasattr(stop, "stop_id") and stop.stop_id is not None:
        return stop.stop_id
    if hasattr(stop, "location_id") and stop.location_id is not None:
        return stop.location_id
    if isinstance(stop, dict):
        return stop.get("stop_id") or stop["location_id"]
    raise AttributeError("Stop object must have stop_id or location_id")


def _extract_stop_sequence(stop: CreateRouteStopRequest | Any) -> int:
    if hasattr(stop, "sequence"):
        return stop.sequence
    if isinstance(stop, dict):
        return stop["sequence"]
    raise AttributeError("Stop object must have sequence")


def update_route(
    session: Session,
    *,
    route_id: UUID,
    driver_id: UUID,
    name: str,
    source_id: UUID,
    dest_id: UUID,
    stops: list[CreateRouteStopRequest] | None = None,
    settings: Settings | None = None,
) -> Route:
    _ = settings or get_settings()
    route_repo = get_route_repo()
    route_stop_repo = get_route_stop_repo()

    route = route_repo.get_by_id_for_update(session, route_id)
    ensure_route_exists(route, route_id=route_id)
    ensure_route_owner(route, driver_id=driver_id)

    normalized_name = normalize_route_name(name)
    stop_location_ids = (
        [_extract_stop_location_id(stop) for stop in stops] if stops else None
    )
    stop_sequences = [_extract_stop_sequence(stop) for stop in stops] if stops else None

    ensure_unique_route_locations(
        source_id=source_id,
        dest_id=dest_id,
        stop_location_ids=stop_location_ids,
    )
    if stop_sequences:
        ensure_valid_intermediate_sequences(
            sequences=stop_sequences,
            total_stops=len(stop_sequences),
        )

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
            current_route_id=route.id,
        )

        route_repo.update(
            session,
            route,
            name=normalized_name,
        )

        route_stop_repo.delete_by_route_id(session, route.id)

        route_stop_repo.create(
            session,
            route_id=route.id,
            location_id=source_id,
            sequence=0,
        )

        if stops:
            sorted_stops = sorted(stops, key=_extract_stop_sequence)
            for stop in sorted_stops:
                route_stop_repo.create(
                    session,
                    route_id=route.id,
                    location_id=_extract_stop_location_id(stop),
                    sequence=_extract_stop_sequence(stop),
                )

        dest_sequence = (len(stops) + 1) if stops else 1
        route_stop_repo.create(
            session,
            route_id=route.id,
            location_id=dest_id,
            sequence=dest_sequence,
        )

        session.commit()
        return route_repo.get_by_id_with_stops(session, route.id) or route
    except Exception:
        session.rollback()
        raise
