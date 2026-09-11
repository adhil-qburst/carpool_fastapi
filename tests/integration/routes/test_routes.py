import pytest
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import joinedload, selectinload

from app.db.session import get_db, get_session_factory
from app.features.location.models.location import Location
from app.features.routes.models.route import Route
from app.features.routes.models.route_stop import RouteStop
from app.features.users.models.user import User


@pytest.fixture
def session():
    SessionLocal = get_session_factory()
    with SessionLocal() as db:
        try:
            yield db
        finally:
            db.close()


@pytest.fixture
def active_user(session):
    user = session.query(User).first()
    return user


def get_a_location(session):
    location = session.query(Location).order_by(func.random()).first()
    return location


def test_db_connected(session):
    result = session.execute(text("SELECT 1"))

    assert result.scalar() == 1


@pytest.mark.skip
@pytest.mark.parametrize(
    "route_name",
    ["morning_route", "evening_route", "night_route"],
)
def test_create_route(
    route_name: str,
    session,
    active_user,
):

    route = Route()
    route.driver = active_user
    route.name = route_name
    route.route_stops = [
        RouteStop(sequence=index, location=get_a_location(session))
        for index in range(0, 10)
    ]

    session.add(route)
    session.commit()

    assert route.id is not None
    assert len(route.route_stops) > 2


def test_get_route_locations(session):

    stmt = (
        select(Location, Route)
        .join(RouteStop, RouteStop.location_id == Location.id)
        .join_from(RouteStop, Route, RouteStop.route_id == Route.id)
        .where(
            Route.id
            == select(Route.id).order_by(func.random()).limit(1).scalar_subquery(),
            RouteStop.sequence.in_([1, 3]),
        )
        .order_by(RouteStop.sequence)
        .options(selectinload(Route.route_stops).selectinload(RouteStop.location))
    )

    results: list[tuple[Location, Route]] = session.execute(stmt).all()

    print("Route name:", results[0][1].name)

    assert results[0][0].id == next(
        stop.location.id for stop in results[0][1].route_stops if stop.sequence == 1
    )
    assert results[1][0].id == next(
        stop.location.id for stop in results[1][1].route_stops if stop.sequence == 3
    )

    assert 1 == 1
