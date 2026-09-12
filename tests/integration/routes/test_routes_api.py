from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.routes.api import routes
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
from app.main import app

TEST_USER_ID = UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def auth_client(client):
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    yield client
    app.dependency_overrides.clear()


def make_fake_route(
    route_id: UUID | None = None,
    driver_id: UUID | None = None,
    name: str = "Office Commute",
    stops: list | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=route_id or uuid4(),
        driver_id=driver_id or TEST_USER_ID,
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
# POST /api/v1/routes
# =============================================================================


def test_create_route_api_success(auth_client, monkeypatch):
    route_id = uuid4()
    source_id = uuid4()
    dest_id = uuid4()

    stop1 = make_fake_stop(route_id=route_id, location_id=source_id, sequence=0)
    stop2 = make_fake_stop(route_id=route_id, location_id=dest_id, sequence=1)
    fake_route = make_fake_route(
        route_id=route_id,
        driver_id=TEST_USER_ID,
        name="Daily Route",
        stops=[stop1, stop2],
    )

    monkeypatch.setattr(
        routes,
        "create_route",
        lambda session, driver_id, name, source_id, dest_id: fake_route,
    )

    response = auth_client.post(
        "/api/v1/routes",
        json={
            "name": "Daily Route",
            "source_id": str(source_id),
            "dest_id": str(dest_id),
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(route_id)
    assert data["name"] == "Daily Route"
    assert data["driver_id"] == str(TEST_USER_ID)
    assert len(data["route_stops"]) == 2


def test_create_route_api_identical_source_dest(auth_client, monkeypatch):
    loc_id = uuid4()

    def fake_create(session, driver_id, name, source_id, dest_id):
        raise IdenticalSourceDestinationError(location_id=source_id)

    monkeypatch.setattr(routes, "create_route", fake_create)

    response = auth_client.post(
        "/api/v1/routes",
        json={
            "name": "Daily Route",
            "source_id": str(loc_id),
            "dest_id": str(loc_id),
        },
    )

    assert response.status_code == 400
    assert "cannot be identical" in response.json()["detail"]


def test_create_route_api_conflict_name(auth_client, monkeypatch):
    def fake_create(session, driver_id, name, source_id, dest_id):
        raise RouteNameAlreadyExistsError(name=name, driver_id=driver_id)

    monkeypatch.setattr(routes, "create_route", fake_create)

    response = auth_client.post(
        "/api/v1/routes",
        json={
            "name": "Existing",
            "source_id": str(uuid4()),
            "dest_id": str(uuid4()),
        },
    )

    assert response.status_code == 409


def test_create_route_api_unauthorized(client):
    app.dependency_overrides[get_db] = lambda: object()

    response = client.post(
        "/api/v1/routes",
        json={
            "name": "Daily Route",
            "source_id": str(uuid4()),
            "dest_id": str(uuid4()),
        },
    )

    assert response.status_code == 401


# =============================================================================
# POST /api/v1/routes/{route_id}/stops
# =============================================================================


def test_add_stop_api_success(auth_client, monkeypatch):
    route_id = uuid4()
    location_id = uuid4()
    fake_stop = make_fake_stop(route_id=route_id, location_id=location_id, sequence=1)

    monkeypatch.setattr(
        routes,
        "add_stop",
        lambda session, route_id, location_id, sequence, driver_id: fake_stop,
    )

    response = auth_client.post(
        f"/api/v1/routes/{route_id}/stops",
        json={
            "location_id": str(location_id),
            "sequence": 1,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(fake_stop.id)
    assert data["route_id"] == str(route_id)
    assert data["location_id"] == str(location_id)
    assert data["sequence"] == 1


def test_add_stop_api_not_found(auth_client, monkeypatch):
    route_id = uuid4()

    def fake_add(session, route_id, location_id, sequence, driver_id):
        raise RouteNotFoundError(route_id=route_id)

    monkeypatch.setattr(routes, "add_stop", fake_add)

    response = auth_client.post(
        f"/api/v1/routes/{route_id}/stops",
        json={"location_id": str(uuid4())},
    )

    assert response.status_code == 404


def test_add_stop_api_forbidden(auth_client, monkeypatch):
    route_id = uuid4()

    def fake_add(session, route_id, location_id, sequence, driver_id):
        raise RouteForbiddenError(route_id=route_id)

    monkeypatch.setattr(routes, "add_stop", fake_add)

    response = auth_client.post(
        f"/api/v1/routes/{route_id}/stops",
        json={"location_id": str(uuid4())},
    )

    assert response.status_code == 403


def test_add_stop_api_duplicate_location(auth_client, monkeypatch):
    route_id = uuid4()

    def fake_add(session, route_id, location_id, sequence, driver_id):
        raise DuplicateStopLocationError(location_id=location_id)

    monkeypatch.setattr(routes, "add_stop", fake_add)

    response = auth_client.post(
        f"/api/v1/routes/{route_id}/stops",
        json={"location_id": str(uuid4())},
    )

    assert response.status_code == 409


def test_add_stop_api_invalid_sequence(auth_client, monkeypatch):
    route_id = uuid4()

    def fake_add(session, route_id, location_id, sequence, driver_id):
        raise InvalidStopSequenceError(sequence=sequence)

    monkeypatch.setattr(routes, "add_stop", fake_add)

    response = auth_client.post(
        f"/api/v1/routes/{route_id}/stops",
        json={"location_id": str(uuid4()), "sequence": 99},
    )

    assert response.status_code == 400


# =============================================================================
# POST /api/v1/routes/{route_id}/stops/swap
# =============================================================================


def test_swap_stops_api_success(auth_client, monkeypatch):
    route_id = uuid4()
    stop_id_1 = uuid4()
    stop_id_2 = uuid4()

    stop1 = make_fake_stop(stop_id=stop_id_1, route_id=route_id, sequence=2)
    stop2 = make_fake_stop(stop_id=stop_id_2, route_id=route_id, sequence=1)

    monkeypatch.setattr(
        routes,
        "swap_stop",
        lambda session, stop_id_1, stop_id_2, route_id, driver_id: (
            stop1,
            stop2,
        ),
    )

    response = auth_client.post(
        f"/api/v1/routes/{route_id}/stops/swap",
        json={
            "stop_id_1": str(stop_id_1),
            "stop_id_2": str(stop_id_2),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == str(stop_id_1)
    assert data[0]["sequence"] == 2
    assert data[1]["id"] == str(stop_id_2)
    assert data[1]["sequence"] == 1


def test_swap_stops_api_same_stop_validation_error(auth_client):
    route_id = uuid4()
    stop_id = uuid4()

    response = auth_client.post(
        f"/api/v1/routes/{route_id}/stops/swap",
        json={
            "stop_id_1": str(stop_id),
            "stop_id_2": str(stop_id),
        },
    )

    assert response.status_code == 422


def test_swap_stops_api_stops_not_same_route(auth_client, monkeypatch):
    route_id = uuid4()
    stop_id_1 = uuid4()
    stop_id_2 = uuid4()

    def fake_swap(session, stop_id_1, stop_id_2, route_id, driver_id):
        raise StopsDoNotBelongToSameRouteError(stop_1_id=stop_id_1, stop_2_id=stop_id_2)

    monkeypatch.setattr(routes, "swap_stop", fake_swap)

    response = auth_client.post(
        f"/api/v1/routes/{route_id}/stops/swap",
        json={
            "stop_id_1": str(stop_id_1),
            "stop_id_2": str(stop_id_2),
        },
    )

    assert response.status_code == 400


def test_swap_stops_api_stop_not_found(auth_client, monkeypatch):
    route_id = uuid4()
    stop_id_1 = uuid4()
    stop_id_2 = uuid4()

    def fake_swap(session, stop_id_1, stop_id_2, route_id, driver_id):
        raise RouteStopNotFoundError(stop_id=stop_id_1)

    monkeypatch.setattr(routes, "swap_stop", fake_swap)

    response = auth_client.post(
        f"/api/v1/routes/{route_id}/stops/swap",
        json={
            "stop_id_1": str(stop_id_1),
            "stop_id_2": str(stop_id_2),
        },
    )

    assert response.status_code == 404


# =============================================================================
# PUT / PATCH /api/v1/routes/{route_id}
# =============================================================================


def test_update_route_api_success_put(auth_client, monkeypatch):
    route_id = uuid4()
    source_id = uuid4()
    dest_id = uuid4()

    stop1 = make_fake_stop(route_id=route_id, location_id=source_id, sequence=0)
    stop2 = make_fake_stop(route_id=route_id, location_id=dest_id, sequence=1)
    fake_route = make_fake_route(
        route_id=route_id,
        driver_id=TEST_USER_ID,
        name="Updated Route",
        stops=[stop1, stop2],
    )

    monkeypatch.setattr(
        routes,
        "update_route",
        lambda session, route_id, driver_id, name, source_id, dest_id, stops: fake_route,
    )

    response = auth_client.put(
        f"/api/v1/routes/{route_id}",
        json={
            "name": "Updated Route",
            "source_id": str(source_id),
            "dest_id": str(dest_id),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(route_id)
    assert data["name"] == "Updated Route"
    assert data["driver_id"] == str(TEST_USER_ID)
    assert len(data["route_stops"]) == 2


def test_update_route_api_success_patch(auth_client, monkeypatch):
    route_id = uuid4()
    source_id = uuid4()
    dest_id = uuid4()

    fake_route = make_fake_route(
        route_id=route_id,
        driver_id=TEST_USER_ID,
        name="Patched Route",
    )

    monkeypatch.setattr(
        routes,
        "update_route",
        lambda session, route_id, driver_id, name, source_id, dest_id, stops: fake_route,
    )

    response = auth_client.patch(
        f"/api/v1/routes/{route_id}",
        json={
            "name": "Patched Route",
            "source_id": str(source_id),
            "dest_id": str(dest_id),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(route_id)
    assert data["name"] == "Patched Route"


def test_update_route_api_not_found(auth_client, monkeypatch):
    route_id = uuid4()

    def fake_update(session, route_id, driver_id, name, source_id, dest_id, stops):
        raise RouteNotFoundError(route_id=route_id)

    monkeypatch.setattr(routes, "update_route", fake_update)

    response = auth_client.put(
        f"/api/v1/routes/{route_id}",
        json={
            "name": "Route",
            "source_id": str(uuid4()),
            "dest_id": str(uuid4()),
        },
    )

    assert response.status_code == 404


def test_update_route_api_forbidden(auth_client, monkeypatch):
    route_id = uuid4()

    def fake_update(session, route_id, driver_id, name, source_id, dest_id, stops):
        raise RouteForbiddenError(route_id=route_id)

    monkeypatch.setattr(routes, "update_route", fake_update)

    response = auth_client.put(
        f"/api/v1/routes/{route_id}",
        json={
            "name": "Route",
            "source_id": str(uuid4()),
            "dest_id": str(uuid4()),
        },
    )

    assert response.status_code == 403


def test_update_route_api_conflict_name(auth_client, monkeypatch):
    route_id = uuid4()

    def fake_update(session, route_id, driver_id, name, source_id, dest_id, stops):
        raise RouteNameAlreadyExistsError(name=name, driver_id=driver_id)

    monkeypatch.setattr(routes, "update_route", fake_update)

    response = auth_client.put(
        f"/api/v1/routes/{route_id}",
        json={
            "name": "Existing",
            "source_id": str(uuid4()),
            "dest_id": str(uuid4()),
        },
    )

    assert response.status_code == 409


def test_update_route_api_identical_source_dest(auth_client, monkeypatch):
    route_id = uuid4()
    loc_id = uuid4()

    def fake_update(session, route_id, driver_id, name, source_id, dest_id, stops):
        raise IdenticalSourceDestinationError(location_id=source_id)

    monkeypatch.setattr(routes, "update_route", fake_update)

    response = auth_client.put(
        f"/api/v1/routes/{route_id}",
        json={
            "name": "Daily Route",
            "source_id": str(loc_id),
            "dest_id": str(loc_id),
        },
    )

    assert response.status_code == 400


def test_update_route_api_duplicate_location(auth_client, monkeypatch):
    route_id = uuid4()

    def fake_update(session, route_id, driver_id, name, source_id, dest_id, stops):
        raise DuplicateStopLocationError(location_id=source_id)

    monkeypatch.setattr(routes, "update_route", fake_update)

    response = auth_client.put(
        f"/api/v1/routes/{route_id}",
        json={
            "name": "Route",
            "source_id": str(uuid4()),
            "dest_id": str(uuid4()),
        },
    )

    assert response.status_code == 409


def test_update_route_api_invalid_sequence(auth_client, monkeypatch):
    route_id = uuid4()

    def fake_update(session, route_id, driver_id, name, source_id, dest_id, stops):
        raise InvalidStopSequenceError(sequence=99)

    monkeypatch.setattr(routes, "update_route", fake_update)

    response = auth_client.put(
        f"/api/v1/routes/{route_id}",
        json={
            "name": "Route",
            "source_id": str(uuid4()),
            "dest_id": str(uuid4()),
        },
    )

    assert response.status_code == 400


def test_update_route_api_unauthorized(client):
    app.dependency_overrides[get_db] = lambda: object()

    response = client.put(
        f"/api/v1/routes/{uuid4()}",
        json={
            "name": "Daily Route",
            "source_id": str(uuid4()),
            "dest_id": str(uuid4()),
        },
    )

    assert response.status_code == 401


# =============================================================================
# GET /api/v1/routes
# =============================================================================


def test_list_routes_api_success(auth_client, monkeypatch):
    route_1 = make_fake_route(name="Route A")
    route_2 = make_fake_route(name="Route B")
    fake_list = [route_1, route_2]

    called_params: dict = {}

    def fake_list_user_routes(session, driver_id, limit, offset):
        called_params["driver_id"] = driver_id
        called_params["limit"] = limit
        called_params["offset"] = offset
        return fake_list, 2

    monkeypatch.setattr(routes, "list_user_routes", fake_list_user_routes)

    response = auth_client.get("/api/v1/routes?page=2&limit=5")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["limit"] == 5
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Route A"
    assert data["items"][1]["name"] == "Route B"
    assert called_params["limit"] == 5
    assert called_params["offset"] == 5


def test_list_routes_api_empty(auth_client, monkeypatch):
    monkeypatch.setattr(
        routes,
        "list_user_routes",
        lambda session, driver_id, limit, offset: ([], 0),
    )

    response = auth_client.get("/api/v1/routes")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["limit"] == 20


def test_list_routes_api_invalid_pagination_domain_error(auth_client, monkeypatch):
    def fake_list(session, driver_id, limit, offset):
        raise InvalidPaginationError(limit=limit, offset=offset)

    monkeypatch.setattr(routes, "list_user_routes", fake_list)

    response = auth_client.get("/api/v1/routes")

    assert response.status_code == 400


def test_list_routes_api_validation_error(auth_client):
    response = auth_client.get("/api/v1/routes?page=0")
    assert response.status_code == 422

    response = auth_client.get("/api/v1/routes?limit=0")
    assert response.status_code == 422


def test_list_routes_api_unauthorized(client):
    app.dependency_overrides[get_db] = lambda: object()

    response = client.get("/api/v1/routes")

    assert response.status_code == 401


# =============================================================================
# DELETE /api/v1/routes/{route_id}
# =============================================================================


def test_delete_route_api_success(auth_client, monkeypatch):
    route_id = uuid4()
    called: dict = {}

    def fake_delete_route(session, route_id, driver_id):
        called["route_id"] = route_id
        called["driver_id"] = driver_id

    monkeypatch.setattr(routes, "delete_route", fake_delete_route)

    response = auth_client.delete(f"/api/v1/routes/{route_id}")

    assert response.status_code == 204
    assert response.text == ""
    assert called["route_id"] == route_id
    assert called["driver_id"] == TEST_USER_ID


def test_delete_route_api_not_found(auth_client, monkeypatch):
    route_id = uuid4()

    def fake_delete_route(session, route_id, driver_id):
        raise RouteNotFoundError(route_id=route_id)

    monkeypatch.setattr(routes, "delete_route", fake_delete_route)

    response = auth_client.delete(f"/api/v1/routes/{route_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found."


def test_delete_route_api_forbidden(auth_client, monkeypatch):
    route_id = uuid4()

    def fake_delete_route(session, route_id, driver_id):
        raise RouteForbiddenError(route_id=route_id, user_id=driver_id)

    monkeypatch.setattr(routes, "delete_route", fake_delete_route)

    response = auth_client.delete(f"/api/v1/routes/{route_id}")

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to access or modify this route."


def test_delete_route_api_invalid_uuid(auth_client):
    response = auth_client.delete("/api/v1/routes/not-a-uuid")
    assert response.status_code == 422


def test_delete_route_api_unauthorized(client):
    app.dependency_overrides[get_db] = lambda: object()

    response = client.delete(f"/api/v1/routes/{uuid4()}")

    assert response.status_code == 401


