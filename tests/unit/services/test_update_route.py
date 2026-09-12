from types import SimpleNamespace
from uuid import UUID, uuid4

import importlib

import pytest

update_route_module = importlib.import_module("app.features.routes.services.update_route")
from app.features.routes.exceptions import (
    DuplicateStopLocationError,
    DuplicateStopSequenceError,
    IdenticalSourceDestinationError,
    InvalidStopSequenceError,
    RouteForbiddenError,
    RouteNameAlreadyExistsError,
    RouteNotFoundError,
)
from app.features.routes.schemas.create_route import CreateRouteStopRequest


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


def test_update_route_success(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    driver_id = uuid4()
    source_id = uuid4()
    dest_id = uuid4()
    mid_id = uuid4()

    fake_route = make_fake_route(route_id=route_id, driver_id=driver_id, name="Old Route")
    created_stops = []
    deleted_route_ids = []

    def fake_update(s, route, name):
        route.name = name
        return route

    fake_route_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, r_id: fake_route,
        get_by_driver_and_name=lambda s, driver_id, name: None,
        update=fake_update,
        get_by_id_with_stops=lambda s, r_id: fake_route,
    )

    def fake_create_stop(s, route_id, location_id, sequence):
        stop = make_fake_stop(route_id=route_id, location_id=location_id, sequence=sequence)
        created_stops.append(stop)
        return stop

    fake_route_stop_repo = SimpleNamespace(
        delete_by_route_id=lambda s, r_id: deleted_route_ids.append(r_id),
        create=fake_create_stop,
    )

    monkeypatch.setattr(update_route_module, "get_route_repo", lambda: fake_route_repo)
    monkeypatch.setattr(update_route_module, "get_route_stop_repo", lambda: fake_route_stop_repo)

    result = update_route_module.update_route(
        session,
        route_id=route_id,
        driver_id=driver_id,
        name="New Route Name",
        source_id=source_id,
        dest_id=dest_id,
        stops=[CreateRouteStopRequest(stop_id=mid_id, sequence=1)],
    )

    assert result.name == "New Route Name"
    assert session.committed is True
    assert route_id in deleted_route_ids
    assert len(created_stops) == 3
    assert created_stops[0].location_id == source_id
    assert created_stops[0].sequence == 0
    assert created_stops[1].location_id == mid_id
    assert created_stops[1].sequence == 1
    assert created_stops[2].location_id == dest_id
    assert created_stops[2].sequence == 2


def test_update_route_keeps_same_name_no_conflict(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    driver_id = uuid4()
    source_id = uuid4()
    dest_id = uuid4()

    fake_route = make_fake_route(route_id=route_id, driver_id=driver_id, name="Daily Commute")

    fake_route_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, r_id: fake_route,
        get_by_driver_and_name=lambda s, driver_id, name: fake_route,
        update=lambda s, route, name: route,
        get_by_id_with_stops=lambda s, r_id: fake_route,
    )

    fake_route_stop_repo = SimpleNamespace(
        delete_by_route_id=lambda s, r_id: None,
        create=lambda s, route_id, location_id, sequence: make_fake_stop(),
    )

    monkeypatch.setattr(update_route_module, "get_route_repo", lambda: fake_route_repo)
    monkeypatch.setattr(update_route_module, "get_route_stop_repo", lambda: fake_route_stop_repo)

    result = update_route_module.update_route(
        session,
        route_id=route_id,
        driver_id=driver_id,
        name="Daily Commute",
        source_id=source_id,
        dest_id=dest_id,
    )

    assert result == fake_route
    assert session.committed is True


def test_update_route_not_found(monkeypatch):
    session = FakeSession()
    fake_route_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, r_id: None,
    )
    monkeypatch.setattr(update_route_module, "get_route_repo", lambda: fake_route_repo)

    with pytest.raises(RouteNotFoundError):
        update_route_module.update_route(
            session,
            route_id=uuid4(),
            driver_id=uuid4(),
            name="Route",
            source_id=uuid4(),
            dest_id=uuid4(),
        )


def test_update_route_forbidden(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    owner_id = uuid4()
    different_driver_id = uuid4()

    fake_route = make_fake_route(route_id=route_id, driver_id=owner_id, name="Route")
    fake_route_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, r_id: fake_route,
    )
    monkeypatch.setattr(update_route_module, "get_route_repo", lambda: fake_route_repo)

    with pytest.raises(RouteForbiddenError):
        update_route_module.update_route(
            session,
            route_id=route_id,
            driver_id=different_driver_id,
            name="Route",
            source_id=uuid4(),
            dest_id=uuid4(),
        )


def test_update_route_name_conflict(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    other_route_id = uuid4()
    driver_id = uuid4()

    current_route = make_fake_route(route_id=route_id, driver_id=driver_id, name="My Route")
    other_route = make_fake_route(route_id=other_route_id, driver_id=driver_id, name="Existing Name")

    fake_route_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, r_id: current_route,
        get_by_driver_and_name=lambda s, driver_id, name: other_route,
    )
    fake_route_stop_repo = SimpleNamespace()

    monkeypatch.setattr(update_route_module, "get_route_repo", lambda: fake_route_repo)
    monkeypatch.setattr(update_route_module, "get_route_stop_repo", lambda: fake_route_stop_repo)

    with pytest.raises(RouteNameAlreadyExistsError):
        update_route_module.update_route(
            session,
            route_id=route_id,
            driver_id=driver_id,
            name="Existing Name",
            source_id=uuid4(),
            dest_id=uuid4(),
        )


def test_update_route_identical_source_destination(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    driver_id = uuid4()
    same_id = uuid4()

    fake_route = make_fake_route(route_id=route_id, driver_id=driver_id)
    fake_route_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, r_id: fake_route,
    )
    monkeypatch.setattr(update_route_module, "get_route_repo", lambda: fake_route_repo)

    with pytest.raises(IdenticalSourceDestinationError):
        update_route_module.update_route(
            session,
            route_id=route_id,
            driver_id=driver_id,
            name="Loop Route",
            source_id=same_id,
            dest_id=same_id,
        )


def test_update_route_duplicate_location(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    driver_id = uuid4()
    source_id = uuid4()
    dest_id = uuid4()

    fake_route = make_fake_route(route_id=route_id, driver_id=driver_id)
    fake_route_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, r_id: fake_route,
    )
    monkeypatch.setattr(update_route_module, "get_route_repo", lambda: fake_route_repo)

    with pytest.raises(DuplicateStopLocationError):
        update_route_module.update_route(
            session,
            route_id=route_id,
            driver_id=driver_id,
            name="Route",
            source_id=source_id,
            dest_id=dest_id,
            stops=[CreateRouteStopRequest(stop_id=source_id, sequence=1)],
        )


def test_update_route_invalid_sequence(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    driver_id = uuid4()

    fake_route = make_fake_route(route_id=route_id, driver_id=driver_id)
    fake_route_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, r_id: fake_route,
    )
    monkeypatch.setattr(update_route_module, "get_route_repo", lambda: fake_route_repo)

    with pytest.raises(InvalidStopSequenceError):
        update_route_module.update_route(
            session,
            route_id=route_id,
            driver_id=driver_id,
            name="Route",
            source_id=uuid4(),
            dest_id=uuid4(),
            stops=[CreateRouteStopRequest(stop_id=uuid4(), sequence=99)],
        )
