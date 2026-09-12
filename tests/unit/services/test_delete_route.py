from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.features.routes.domain.enums import RouteStatus
from app.features.routes.exceptions import (
    RouteForbiddenError,
    RouteNotFoundError,
)
from app.features.routes.services.delete_route import delete_route


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


class FakeRouteRepo:
    def __init__(self, route=None):
        self.route = route
        self.soft_deleted = False

    def get_by_id_for_update(self, session, route_id: UUID, status: RouteStatus | None = None):
        if self.route and self.route.id == route_id:
            if status is not None and getattr(self.route, "status", None) != status:
                return None
            return self.route
        return None

    def soft_delete(self, session, route):
        self.soft_deleted = True
        route.status = RouteStatus.INACTIVE
        return route


def make_fake_route(
    route_id: UUID | None = None,
    driver_id: UUID | None = None,
    name: str = "Test Route",
    status: RouteStatus = RouteStatus.ACTIVE,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=route_id or uuid4(),
        driver_id=driver_id or uuid4(),
        name=name,
        status=status,
        route_stops=[],
    )


def test_delete_route_success(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    driver_id = uuid4()
    fake_route = make_fake_route(route_id=route_id, driver_id=driver_id)
    fake_repo = FakeRouteRepo(route=fake_route)

    monkeypatch.setattr(
        "app.features.routes.services.delete_route.get_route_repo",
        lambda: fake_repo,
    )

    delete_route(session, route_id=route_id, driver_id=driver_id)

    assert fake_repo.soft_deleted is True
    assert fake_route.status == RouteStatus.INACTIVE
    assert session.committed is True
    assert session.rolled_back is False


def test_delete_route_not_found(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    driver_id = uuid4()
    fake_repo = FakeRouteRepo(route=None)

    monkeypatch.setattr(
        "app.features.routes.services.delete_route.get_route_repo",
        lambda: fake_repo,
    )

    with pytest.raises(RouteNotFoundError):
        delete_route(session, route_id=route_id, driver_id=driver_id)

    assert session.committed is False
    assert session.rolled_back is True


def test_delete_route_already_inactive(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    driver_id = uuid4()
    inactive_route = make_fake_route(
        route_id=route_id,
        driver_id=driver_id,
        status=RouteStatus.INACTIVE,
    )
    fake_repo = FakeRouteRepo(route=inactive_route)

    monkeypatch.setattr(
        "app.features.routes.services.delete_route.get_route_repo",
        lambda: fake_repo,
    )

    with pytest.raises(RouteNotFoundError):
        delete_route(session, route_id=route_id, driver_id=driver_id)

    assert session.committed is False
    assert session.rolled_back is True


def test_delete_route_forbidden_for_non_owner(monkeypatch):
    session = FakeSession()
    route_id = uuid4()
    owner_id = uuid4()
    other_user_id = uuid4()
    fake_route = make_fake_route(route_id=route_id, driver_id=owner_id)
    fake_repo = FakeRouteRepo(route=fake_route)

    monkeypatch.setattr(
        "app.features.routes.services.delete_route.get_route_repo",
        lambda: fake_repo,
    )

    with pytest.raises(RouteForbiddenError):
        delete_route(session, route_id=route_id, driver_id=other_user_id)

    assert fake_repo.soft_deleted is False
    assert fake_route.status == RouteStatus.ACTIVE
    assert session.committed is False
    assert session.rolled_back is True
