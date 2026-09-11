from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.features.routes.models.route_stop import RouteStop


class RouteStopRepo:
    def create(
        self,
        session: Session,
        *,
        route_id: UUID,
        location_id: UUID,
        sequence: int,
    ) -> RouteStop:
        stop = RouteStop(
            route_id=route_id,
            location_id=location_id,
            sequence=sequence,
        )
        session.add(stop)
        session.flush()
        return stop

    def create_many(
        self,
        session: Session,
        *,
        stops_data: list[dict[str, Any]],
    ) -> list[RouteStop]:
        stops = [
            RouteStop(
                route_id=data["route_id"],
                location_id=data["location_id"],
                sequence=data["sequence"],
            )
            for data in stops_data
        ]
        session.add_all(stops)
        session.flush()
        return stops

    def get_by_id(self, session: Session, stop_id: UUID) -> RouteStop | None:
        return session.get(RouteStop, stop_id)

    def get_by_id_for_update(
        self,
        session: Session,
        stop_id: UUID,
    ) -> RouteStop | None:
        return session.scalar(
            select(RouteStop).where(RouteStop.id == stop_id).with_for_update()
        )

    def list_by_route_id(
        self,
        session: Session,
        route_id: UUID,
    ) -> list[RouteStop]:
        return list(
            session.scalars(
                select(RouteStop)
                .where(RouteStop.route_id == route_id)
                .options(joinedload(RouteStop.location))
                .order_by(RouteStop.sequence.asc())
            ).all()
        )

    def list_by_location_id(
        self,
        session: Session,
        location_id: UUID,
    ) -> list[RouteStop]:
        return list(
            session.scalars(
                select(RouteStop)
                .where(RouteStop.location_id == location_id)
                .order_by(RouteStop.route_id, RouteStop.sequence.asc())
            ).all()
        )

    def delete(self, session: Session, stop: RouteStop) -> None:
        session.delete(stop)
        session.flush()

    def delete_by_route_id(self, session: Session, route_id: UUID) -> None:
        session.execute(delete(RouteStop).where(RouteStop.route_id == route_id))
        session.flush()


def get_route_stop_repo() -> RouteStopRepo:
    return RouteStopRepo()
