from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased, joinedload, selectinload

from app.features.routes.domain.enums import RouteStatus
from app.features.routes.models.route import Route
from app.features.routes.models.route_stop import RouteStop
from app.features.routes.repositories.route_stop_repo import (
    RouteStopRepo,
    get_route_stop_repo,
)


class RouteRepo:
    def create(
        self,
        session: Session,
        *,
        name: str,
        driver_id: UUID,
        status: RouteStatus = RouteStatus.ACTIVE,
    ) -> Route:
        route = Route(
            name=name,
            driver_id=driver_id,
            status=status,
        )
        session.add(route)
        session.flush()
        return route

    def get_by_id(
        self,
        session: Session,
        route_id: UUID,
        *,
        status: RouteStatus | None = None,
    ) -> Route | None:
        if status is not None:
            return session.scalar(
                select(Route).where(Route.id == route_id, Route.status == status)
            )
        return session.get(Route, route_id)

    def get_by_id_for_update(
        self,
        session: Session,
        route_id: UUID,
        *,
        status: RouteStatus | None = None,
    ) -> Route | None:
        stmt = select(Route).where(Route.id == route_id).with_for_update()
        if status is not None:
            stmt = stmt.where(Route.status == status)
        return session.scalar(stmt)

    def get_by_id_with_stops(
        self,
        session: Session,
        route_id: UUID,
        *,
        status: RouteStatus | None = None,
    ) -> Route | None:
        stmt = (
            select(Route)
            .where(Route.id == route_id)
            .options(
                selectinload(Route.route_stops).joinedload(RouteStop.location),
            )
        )
        if status is not None:
            stmt = stmt.where(Route.status == status)
        return session.scalar(stmt)

    def get_by_driver_and_name(
        self,
        session: Session,
        *,
        driver_id: UUID,
        name: str,
        status: RouteStatus | None = RouteStatus.ACTIVE,
    ) -> Route | None:
        stmt = select(Route).where(
            Route.driver_id == driver_id,
            Route.name == name,
        )
        if status is not None:
            stmt = stmt.where(Route.status == status)
        return session.scalar(stmt)

    def list_by_driver_id(
        self,
        session: Session,
        driver_id: UUID,
        *,
        limit: int | None = None,
        offset: int = 0,
        status: RouteStatus | None = RouteStatus.ACTIVE,
    ) -> list[Route]:
        stmt = (
            select(Route)
            .where(Route.driver_id == driver_id)
            .options(
                selectinload(Route.route_stops).joinedload(RouteStop.location),
            )
            .order_by(Route.name.asc())
        )
        if status is not None:
            stmt = stmt.where(Route.status == status)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset > 0:
            stmt = stmt.offset(offset)
        return list(session.scalars(stmt).all())

    def count_by_driver_id(
        self,
        session: Session,
        driver_id: UUID,
        *,
        status: RouteStatus | None = RouteStatus.ACTIVE,
    ) -> int:
        stmt = select(func.count(Route.id)).where(Route.driver_id == driver_id)
        if status is not None:
            stmt = stmt.where(Route.status == status)
        return session.scalar(stmt) or 0

    def find_by_locations(
        self,
        session: Session,
        *,
        source_location_id: UUID,
        destination_location_id: UUID,
        status: RouteStatus | None = RouteStatus.ACTIVE,
    ) -> list[Route]:
        source_stop = aliased(RouteStop)
        dest_stop = aliased(RouteStop)

        stmt = (
            select(Route)
            .join(source_stop, source_stop.route_id == Route.id)
            .join(dest_stop, dest_stop.route_id == Route.id)
            .where(
                source_stop.location_id == source_location_id,
                dest_stop.location_id == destination_location_id,
                source_stop.sequence < dest_stop.sequence,
            )
            .options(
                selectinload(Route.route_stops).joinedload(RouteStop.location),
            )
            .order_by(Route.name.asc())
        )
        if status is not None:
            stmt = stmt.where(Route.status == status)
        return list(session.scalars(stmt).all())

    def update(
        self,
        session: Session,
        route: Route,
        *,
        name: str | None = None,
        status: RouteStatus | None = None,
    ) -> Route:
        if name is not None:
            route.name = name
        if status is not None:
            route.status = status
        session.flush()
        return route

    def soft_delete(self, session: Session, route: Route) -> Route:
        route.status = RouteStatus.INACTIVE
        session.flush()
        return route

    def delete(self, session: Session, route: Route) -> None:
        session.delete(route)
        session.flush()


def get_route_repo() -> RouteRepo:
    return RouteRepo()
