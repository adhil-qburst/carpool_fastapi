from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.trips.api import trips
from app.features.trips.domain.enums import TripStatus
from app.features.trips.exceptions import (
    InvalidAvailableSeatsError,
    PastDepartureError,
    RouteForbiddenError,
    RouteNotFoundError,
    TripCannotBeDeletedError,
    TripCannotBeModifiedError,
    TripForbiddenError,
    TripNotFoundError,
)
from app.main import app

TEST_USER_ID = UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def auth_client(client):
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    yield client
    app.dependency_overrides.clear()


def make_fake_trip(
    trip_id: UUID | None = None,
    route_id: UUID | None = None,
    driver_id: UUID | None = None,
    vehicle_id: UUID | None = None,
    departure_date: date | None = None,
    departure_time: time | None = None,
    available_seats: int = 3,
    status: TripStatus = TripStatus.SCHEDULED,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    future_date = date.today() + timedelta(days=2)
    return SimpleNamespace(
        id=trip_id or uuid4(),
        route_id=route_id or uuid4(),
        driver_id=driver_id or TEST_USER_ID,
        vehicle_id=vehicle_id or uuid4(),
        departure_date=departure_date or future_date,
        departure_time=departure_time or time(10, 0),
        available_seats=available_seats,
        status=status,
        created_at=now,
        updated_at=now,
    )


# =============================================================================
# POST /api/v1/trips
# =============================================================================


def test_create_trip_api_success(auth_client, monkeypatch):
    trip_id = uuid4()
    route_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=2)
    fake_trip = make_fake_trip(
        trip_id=trip_id,
        route_id=route_id,
        driver_id=TEST_USER_ID,
        vehicle_id=vehicle_id,
        departure_date=future_date,
        departure_time=time(14, 0),
        available_seats=4,
    )

    monkeypatch.setattr(
        trips,
        "create_trip",
        lambda session, driver_id, payload: fake_trip,
    )

    response = auth_client.post(
        "/api/v1/trips",
        json={
            "route_id": str(route_id),
            "vehicle_id": str(vehicle_id),
            "departure_date": str(future_date),
            "departure_time": "14:00:00",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(trip_id)
    assert data["route_id"] == str(route_id)
    assert data["vehicle_id"] == str(vehicle_id)
    assert data["available_seats"] == 4
    assert data["status"] == "scheduled"


def test_create_trip_api_route_not_found(auth_client, monkeypatch):
    route_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=2)

    def fake_create(*args, **kwargs):
        raise RouteNotFoundError(route_id=route_id)

    monkeypatch.setattr(trips, "create_trip", fake_create)

    response = auth_client.post(
        "/api/v1/trips",
        json={
            "route_id": str(route_id),
            "vehicle_id": str(vehicle_id),
            "departure_date": str(future_date),
            "departure_time": "14:00:00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found."


def test_create_trip_api_vehicle_not_found(auth_client, monkeypatch):
    from app.features.vehicles.exceptions import VehicleNotFoundError

    route_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=2)

    def fake_create(*args, **kwargs):
        raise VehicleNotFoundError(vehicle_id=vehicle_id)

    monkeypatch.setattr(trips, "create_trip", fake_create)

    response = auth_client.post(
        "/api/v1/trips",
        json={
            "route_id": str(route_id),
            "vehicle_id": str(vehicle_id),
            "departure_date": str(future_date),
            "departure_time": "14:00:00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Vehicle not found."


def test_create_trip_api_vehicle_forbidden(auth_client, monkeypatch):
    from app.features.vehicles.exceptions import VehicleForbiddenError

    route_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=2)

    def fake_create(*args, **kwargs):
        raise VehicleForbiddenError(vehicle_id=vehicle_id)

    monkeypatch.setattr(trips, "create_trip", fake_create)

    response = auth_client.post(
        "/api/v1/trips",
        json={
            "route_id": str(route_id),
            "vehicle_id": str(vehicle_id),
            "departure_date": str(future_date),
            "departure_time": "14:00:00",
        },
    )

    assert response.status_code == 403


def test_create_trip_api_route_forbidden(auth_client, monkeypatch):
    route_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=2)

    def fake_create(*args, **kwargs):
        raise RouteForbiddenError(route_id=route_id)

    monkeypatch.setattr(trips, "create_trip", fake_create)

    response = auth_client.post(
        "/api/v1/trips",
        json={
            "route_id": str(route_id),
            "vehicle_id": str(vehicle_id),
            "departure_date": str(future_date),
            "departure_time": "14:00:00",
        },
    )

    assert response.status_code == 403


def test_create_trip_api_past_departure(auth_client, monkeypatch):
    route_id = uuid4()
    vehicle_id = uuid4()
    past_date = date.today() - timedelta(days=1)

    def fake_create(*args, **kwargs):
        raise PastDepartureError()

    monkeypatch.setattr(trips, "create_trip", fake_create)

    response = auth_client.post(
        "/api/v1/trips",
        json={
            "route_id": str(route_id),
            "vehicle_id": str(vehicle_id),
            "departure_date": str(past_date),
            "departure_time": "14:00:00",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Departure date and time must be in the future."



# =============================================================================
# GET /api/v1/trips
# =============================================================================


def test_list_trips_api_success(auth_client, monkeypatch):
    trip = make_fake_trip(driver_id=TEST_USER_ID)
    monkeypatch.setattr(
        trips,
        "list_driver_trips",
        lambda session, driver_id, limit, offset: ([trip], 1),
    )

    response = auth_client.get("/api/v1/trips?page=1&limit=20")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(trip.id)


# =============================================================================
# GET /api/v1/trips/{trip_id}
# =============================================================================


def test_get_trip_by_id_api_success(auth_client, monkeypatch):
    trip_id = uuid4()
    trip = make_fake_trip(trip_id=trip_id, driver_id=TEST_USER_ID)
    monkeypatch.setattr(
        trips,
        "get_trip",
        lambda session, trip_id, driver_id: trip,
    )

    response = auth_client.get(f"/api/v1/trips/{trip_id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(trip_id)


def test_get_trip_by_id_api_not_found(auth_client, monkeypatch):
    trip_id = uuid4()

    def fake_get(*args, **kwargs):
        raise TripNotFoundError(trip_id=trip_id)

    monkeypatch.setattr(trips, "get_trip", fake_get)

    response = auth_client.get(f"/api/v1/trips/{trip_id}")
    assert response.status_code == 404


# =============================================================================
# PATCH /api/v1/trips/{trip_id}
# =============================================================================


def test_update_trip_api_success(auth_client, monkeypatch):
    trip_id = uuid4()
    vehicle_id = uuid4()
    updated = make_fake_trip(trip_id=trip_id, driver_id=TEST_USER_ID, vehicle_id=vehicle_id, available_seats=5)

    monkeypatch.setattr(
        trips,
        "update_trip",
        lambda session, trip_id, driver_id, payload: updated,
    )

    response = auth_client.patch(
        f"/api/v1/trips/{trip_id}",
        json={"vehicle_id": str(vehicle_id)},
    )
    assert response.status_code == 200
    assert response.json()["available_seats"] == 5
    assert response.json()["vehicle_id"] == str(vehicle_id)


def test_update_trip_api_cannot_modify(auth_client, monkeypatch):
    trip_id = uuid4()
    vehicle_id = uuid4()

    def fake_update(*args, **kwargs):
        raise TripCannotBeModifiedError("cancelled")

    monkeypatch.setattr(trips, "update_trip", fake_update)

    response = auth_client.patch(
        f"/api/v1/trips/{trip_id}",
        json={"vehicle_id": str(vehicle_id)},
    )
    assert response.status_code == 400
    assert "cannot be modified" in response.json()["detail"]


# =============================================================================
# DELETE /api/v1/trips/{trip_id}
# =============================================================================


def test_delete_trip_api_success(auth_client, monkeypatch):
    trip_id = uuid4()
    monkeypatch.setattr(
        trips,
        "delete_trip",
        lambda session, trip_id, driver_id: None,
    )

    response = auth_client.delete(f"/api/v1/trips/{trip_id}")
    assert response.status_code == 204


def test_delete_trip_api_completed_cannot_delete(auth_client, monkeypatch):
    trip_id = uuid4()

    def fake_delete(*args, **kwargs):
        raise TripCannotBeDeletedError("completed")

    monkeypatch.setattr(trips, "delete_trip", fake_delete)

    response = auth_client.delete(f"/api/v1/trips/{trip_id}")
    assert response.status_code == 400
    assert "cannot be deleted" in response.json()["detail"]
