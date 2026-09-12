from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

import app.features.routes.services.add_stop as add_stop_service
import app.features.routes.services.create_route as create_route_service
import app.features.routes.services.list_routes as list_routes_service
import app.features.routes.services.swap_stop as swap_stop_service
from app.features.routes.exceptions import (
    CannotSwapSameStopError,
    DuplicateStopLocationError,
    IdenticalSourceDestinationError,
    InvalidPaginationError,
    InvalidStopSequenceError,
    RouteForbiddenError,
    RouteNameAlreadyExistsError,
    RouteNotFoundError,
    RouteStopNotFoundError,
    StopsDoNotBelongToSameRouteError,
)


class FakeSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.flushed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def flush(self):
        self.flushed = True


def make_fake_route(
    route_id: UUID | None = None,
    driver_id: UUID | None = None,
    name: str = "Test Route",
    stops: list | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=route_id or uuid4(),
        driver_id=driver_id or uuid4(),
        name=name,
        route_stops=stops or [],
    )


def make_fake_stop(
    stop_id: UUID | None = None,
    route_id: UUID | None = None,
    location_id: UUID | None = None,
    sequence: int = 0,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=stop_id or uuid4(),
        route_id=route_id or uuid4(),
        location_id=location_id or uuid4(),
        sequence=sequence,
    )


# =============================================================================
# create_route
# =============================================================================


def test_create_route_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    source_id = uuid4()
    dest_id = uuid4()

    fake_route = make_fake_route(driver_id=driver_id, name="Daily Commute")
    created_stops = []

    fake_route_repo = SimpleNamespace(
        get_by_driver_and_name=lambda s, driver_id, name: None,
        create=lambda s, name, driver_id: fake_route,
        get_by_id_with_stops=lambda s, route_id: fake_route,
    )

    def fake_create_stop(s, route_id, location_id, sequence):
        stop = make_fake_stop(
            route_id=route_id, location_id=location_id, sequence=sequence
        )
        created_stops.append(stop)
        return stop

    fake_route_stop_repo = SimpleNamespace(create=fake_create_stop)

    monkeypatch.setattr(create_route_service, "get_route_repo", lambda: fake_route_repo)
    monkeypatch.setattr(
        create_route_service, "get_route_stop_repo", lambda: fake_route_stop_repo
    )

    result = create_route_service.create_route(
        session,
        driver_id=driver_id,
        name="Daily Commute",
        source_id=source_id,
        dest_id=dest_id,
    )

    assert result == fake_route
    assert session.committed is True
    assert session.rolled_back is False
    assert len(created_stops) == 2
    assert created_stops[0].location_id == source_id
    assert created_stops[0].sequence == 0
    assert created_stops[1].location_id == dest_id
    assert created_stops[1].sequence == 1


def test_create_route_identical_source_dest_raises_error():
    session = FakeSession()
    loc_id = uuid4()

    with pytest.raises(IdenticalSourceDestinationError):
        create_route_service.create_route(
            session,
            driver_id=uuid4(),
            name="Test",
            source_id=loc_id,
            dest_id=loc_id,
        )


def test_create_route_duplicate_name_raises_error(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    existing_route = make_fake_route(driver_id=driver_id, name="Office")

    fake_route_repo = SimpleNamespace(
        get_by_driver_and_name=lambda s, driver_id, name: existing_route,
    )

    monkeypatch.setattr(create_route_service, "get_route_repo", lambda: fake_route_repo)

    with pytest.raises(RouteNameAlreadyExistsError):
        create_route_service.create_route(
            session,
            driver_id=driver_id,
            name="Office",
            source_id=uuid4(),
            dest_id=uuid4(),
        )
    assert session.rollback is not None


# =============================================================================
# add_stop
# =============================================================================


def test_add_stop_success_default_sequence(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    driver_id = uuid4()
    loc1 = uuid4()
    loc2 = uuid4()
    loc_new = uuid4()

    route = make_fake_route(route_id=route_id, driver_id=driver_id)
    stop0 = make_fake_stop(route_id=route_id, location_id=loc1, sequence=0)
    stop1 = make_fake_stop(route_id=route_id, location_id=loc2, sequence=1)
    existing_stops = [stop0, stop1]

    fake_route_repo = SimpleNamespace(
        get_by_id=lambda s, r_id: route,
    )

    created_stop = make_fake_stop(route_id=route_id, location_id=loc_new, sequence=1)
    fake_route_stop_repo = SimpleNamespace(
        list_by_route_id=lambda s, r_id: existing_stops,
        create=lambda s, route_id, location_id, sequence: created_stop,
    )

    monkeypatch.setattr(add_stop_service, "get_route_repo", lambda: fake_route_repo)
    monkeypatch.setattr(
        add_stop_service, "get_route_stop_repo", lambda: fake_route_stop_repo
    )

    res = add_stop_service.add_stop(
        session,
        route_id=route_id,
        location_id=loc_new,
        driver_id=driver_id,
    )

    assert res == created_stop
    # Destination stop (stop1) should have been shifted from sequence 1 to 2
    assert stop1.sequence == 2
    assert stop0.sequence == 0
    assert session.flushed is True
    assert session.committed is True


def test_add_stop_duplicate_location_raises_error(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    driver_id = uuid4()
    loc1 = uuid4()

    route = make_fake_route(route_id=route_id, driver_id=driver_id)
    stop0 = make_fake_stop(route_id=route_id, location_id=loc1, sequence=0)

    fake_route_repo = SimpleNamespace(get_by_id=lambda s, r_id: route)
    fake_route_stop_repo = SimpleNamespace(list_by_route_id=lambda s, r_id: [stop0])

    monkeypatch.setattr(add_stop_service, "get_route_repo", lambda: fake_route_repo)
    monkeypatch.setattr(
        add_stop_service, "get_route_stop_repo", lambda: fake_route_stop_repo
    )

    with pytest.raises(DuplicateStopLocationError):
        add_stop_service.add_stop(
            session,
            route_id=route_id,
            location_id=loc1,
        )


def test_add_stop_not_owner_raises_error(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    owner_id = uuid4()
    other_driver_id = uuid4()

    route = make_fake_route(route_id=route_id, driver_id=owner_id)
    fake_route_repo = SimpleNamespace(get_by_id=lambda s, r_id: route)

    monkeypatch.setattr(add_stop_service, "get_route_repo", lambda: fake_route_repo)

    with pytest.raises(RouteForbiddenError):
        add_stop_service.add_stop(
            session,
            route_id=route_id,
            location_id=uuid4(),
            driver_id=other_driver_id,
        )


def test_add_stop_invalid_sequence_raises_error(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    driver_id = uuid4()

    route = make_fake_route(route_id=route_id, driver_id=driver_id)
    fake_route_repo = SimpleNamespace(get_by_id=lambda s, r_id: route)
    fake_route_stop_repo = SimpleNamespace(list_by_route_id=lambda s, r_id: [])

    monkeypatch.setattr(add_stop_service, "get_route_repo", lambda: fake_route_repo)
    monkeypatch.setattr(
        add_stop_service, "get_route_stop_repo", lambda: fake_route_stop_repo
    )

    with pytest.raises(InvalidStopSequenceError):
        add_stop_service.add_stop(
            session,
            route_id=route_id,
            location_id=uuid4(),
            sequence=99,
        )


# =============================================================================
# swap_stop
# =============================================================================


def test_swap_stop_success(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    stop_id_1 = uuid4()
    stop_id_2 = uuid4()

    stop_1 = make_fake_stop(stop_id=stop_id_1, route_id=route_id, sequence=1)
    stop_2 = make_fake_stop(stop_id=stop_id_2, route_id=route_id, sequence=2)

    def fake_get_stop(s, s_id):
        if s_id == stop_id_1:
            return stop_1
        if s_id == stop_id_2:
            return stop_2
        return None

    fake_route_stop_repo = SimpleNamespace(
        get_by_id_for_update=fake_get_stop,
    )

    monkeypatch.setattr(
        swap_stop_service, "get_route_stop_repo", lambda: fake_route_stop_repo
    )

    res1, res2 = swap_stop_service.swap_stop(
        session,
        stop_id_1=stop_id_1,
        stop_id_2=stop_id_2,
        route_id=route_id,
    )

    assert res1.sequence == 2
    assert res2.sequence == 1
    assert session.flushed is True
    assert session.committed is True


def test_swap_stop_same_id_raises_error():
    session = FakeSession()
    stop_id = uuid4()

    with pytest.raises(CannotSwapSameStopError):
        swap_stop_service.swap_stop(
            session,
            stop_id_1=stop_id,
            stop_id_2=stop_id,
        )


def test_swap_stop_different_routes_raises_error(monkeypatch):
    session = FakeSession()
    stop_id_1 = uuid4()
    stop_id_2 = uuid4()

    stop_1 = make_fake_stop(stop_id=stop_id_1, route_id=uuid4(), sequence=1)
    stop_2 = make_fake_stop(stop_id=stop_id_2, route_id=uuid4(), sequence=2)

    def fake_get_stop(s, s_id):
        if s_id == stop_id_1:
            return stop_1
        if s_id == stop_id_2:
            return stop_2
        return None

    fake_route_stop_repo = SimpleNamespace(get_by_id_for_update=fake_get_stop)
    monkeypatch.setattr(
        swap_stop_service, "get_route_stop_repo", lambda: fake_route_stop_repo
    )

    with pytest.raises(StopsDoNotBelongToSameRouteError):
        swap_stop_service.swap_stop(
            session,
            stop_id_1=stop_id_1,
            stop_id_2=stop_id_2,
        )


# =============================================================================
# list_user_routes
# =============================================================================


def test_list_user_routes_returns_driver_routes_and_total(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()

    fake_routes = [
        make_fake_route(driver_id=driver_id, name="Morning Commute"),
        make_fake_route(driver_id=driver_id, name="Evening Commute"),
    ]

    called_with: dict = {}

    def fake_list_by_driver_id(s, driver_id, limit=20, offset=0, status=None):
        called_with["driver_id"] = driver_id
        called_with["limit"] = limit
        called_with["offset"] = offset
        called_with["status"] = status
        return fake_routes

    fake_route_repo = SimpleNamespace(
        list_by_driver_id=fake_list_by_driver_id,
        count_by_driver_id=lambda s, driver_id, **kwargs: 2,
    )
    monkeypatch.setattr(list_routes_service, "get_route_repo", lambda: fake_route_repo)

    items, total = list_routes_service.list_user_routes(
        session, driver_id, limit=10, offset=5
    )

    assert items == fake_routes
    assert total == 2
    assert called_with["driver_id"] == driver_id
    assert called_with["limit"] == 10
    assert called_with["offset"] == 5
    assert called_with["status"] == "active"


def test_list_user_routes_returns_empty_list_when_no_routes(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()

    fake_route_repo = SimpleNamespace(
        list_by_driver_id=lambda s, driver_id, limit=20, offset=0, status=None: [],
        count_by_driver_id=lambda s, driver_id, **kwargs: 0,
    )
    monkeypatch.setattr(list_routes_service, "get_route_repo", lambda: fake_route_repo)

    items, total = list_routes_service.list_user_routes(session, driver_id)

    assert items == []
    assert total == 0


def test_list_user_routes_invalid_pagination_raises(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()

    with pytest.raises(InvalidPaginationError):
        list_routes_service.list_user_routes(session, driver_id, limit=0)

    with pytest.raises(InvalidPaginationError):
        list_routes_service.list_user_routes(session, driver_id, offset=-1)
