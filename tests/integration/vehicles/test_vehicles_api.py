from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.vehicles.api import vehicles
from app.features.vehicles.exceptions import (
    VehicleForbiddenError,
    VehicleNotFoundError,
    VehicleRegistrationAlreadyExistsError,
)
from app.main import app

TEST_USER_ID = UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def auth_client(client):
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    yield client
    app.dependency_overrides.clear()


def make_fake_vehicle(
    vehicle_id: UUID | None = None,
    driver_id: UUID | None = None,
    make: str = "Toyota",
    model: str = "Prius",
    registration_number: str = "KL-01-AB-1234",
    total_seats: int = 4,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=vehicle_id or uuid4(),
        driver_id=driver_id or TEST_USER_ID,
        make=make,
        model=model,
        registration_number=registration_number,
        total_seats=total_seats,
        created_at=now,
        updated_at=now,
    )


# =============================================================================
# POST /api/v1/vehicles
# =============================================================================


def test_create_vehicle_success(auth_client, monkeypatch):
    vehicle_id = uuid4()
    fake_vehicle = make_fake_vehicle(
        vehicle_id=vehicle_id,
        driver_id=TEST_USER_ID,
        make="Toyota",
        model="Prius",
        registration_number="KL-01-AB-1234",
        total_seats=4,
    )

    monkeypatch.setattr(
        vehicles,
        "create_vehicle",
        lambda db, driver_id, payload: fake_vehicle,
    )

    response = auth_client.post(
        "/api/v1/vehicles",
        json={
            "make": "Toyota",
            "model": "Prius",
            "registration_number": "KL-01-AB-1234",
            "total_seats": 4,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(vehicle_id)
    assert data["driver_id"] == str(TEST_USER_ID)
    assert data["make"] == "Toyota"
    assert data["model"] == "Prius"
    assert data["registration_number"] == "KL-01-AB-1234"
    assert data["total_seats"] == 4


@pytest.mark.parametrize(
    "invalid_payload",
    [
        # Missing make
        {
            "model": "Prius",
            "registration_number": "KL-01-AB-1234",
            "total_seats": 4,
        },
        # Blank make
        {
            "make": "   ",
            "model": "Prius",
            "registration_number": "KL-01-AB-1234",
            "total_seats": 4,
        },
        # Missing model
        {
            "make": "Toyota",
            "registration_number": "KL-01-AB-1234",
            "total_seats": 4,
        },
        # Missing registration number
        {
            "make": "Toyota",
            "model": "Prius",
            "total_seats": 4,
        },
        # Blank registration number
        {
            "make": "Toyota",
            "model": "Prius",
            "registration_number": "   ",
            "total_seats": 4,
        },
        # Total seats <= 0
        {
            "make": "Toyota",
            "model": "Prius",
            "registration_number": "KL-01-AB-1234",
            "total_seats": 0,
        },
        # Total seats > 50
        {
            "make": "Toyota",
            "model": "Prius",
            "registration_number": "KL-01-AB-1234",
            "total_seats": 51,
        },
    ],
)
def test_create_vehicle_validation_error(auth_client, invalid_payload):
    response = auth_client.post(
        "/api/v1/vehicles",
        json=invalid_payload,
    )

    assert response.status_code == 422


def test_create_vehicle_duplicate_registration_returns_409(auth_client, monkeypatch):
    def fake_create_vehicle(db, driver_id, payload):
        raise VehicleRegistrationAlreadyExistsError(payload.registration_number)

    monkeypatch.setattr(vehicles, "create_vehicle", fake_create_vehicle)

    response = auth_client.post(
        "/api/v1/vehicles",
        json={
            "make": "Toyota",
            "model": "Prius",
            "registration_number": "KL-01-AB-1234",
            "total_seats": 4,
        },
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_vehicle_unauthenticated(client):
    app.dependency_overrides[get_db] = lambda: object()

    response = client.post(
        "/api/v1/vehicles",
        json={
            "make": "Toyota",
            "model": "Prius",
            "registration_number": "KL-01-AB-1234",
            "total_seats": 4,
        },
    )

    assert response.status_code == 401


# =============================================================================
# GET /api/v1/vehicles
# =============================================================================


def test_list_vehicles_success(auth_client, monkeypatch):
    fake_list = [
        make_fake_vehicle(
            make="Toyota",
            model="Prius",
            registration_number="KL-01-AB-1234",
        ),
        make_fake_vehicle(
            make="Honda",
            model="Civic",
            registration_number="KL-01-CD-5678",
        ),
    ]

    monkeypatch.setattr(
        vehicles,
        "list_user_vehicles",
        lambda db, driver_id: fake_list,
    )

    response = auth_client.get("/api/v1/vehicles")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["make"] == "Toyota"
    assert data[1]["make"] == "Honda"


def test_list_vehicles_unauthenticated(client):
    app.dependency_overrides[get_db] = lambda: object()

    response = client.get("/api/v1/vehicles")

    assert response.status_code == 401


# =============================================================================
# GET /api/v1/vehicles/{vehicle_id}
# =============================================================================


def test_get_vehicle_success(auth_client, monkeypatch):
    vehicle_id = uuid4()
    fake_vehicle = make_fake_vehicle(
        vehicle_id=vehicle_id,
        driver_id=TEST_USER_ID,
    )

    monkeypatch.setattr(
        vehicles,
        "get_vehicle",
        lambda db, vehicle_id, driver_id: fake_vehicle,
    )

    response = auth_client.get(f"/api/v1/vehicles/{vehicle_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(vehicle_id)


def test_get_vehicle_not_found(auth_client, monkeypatch):
    vehicle_id = uuid4()

    def fake_get_vehicle(db, vehicle_id, driver_id):
        raise VehicleNotFoundError(vehicle_id)

    monkeypatch.setattr(vehicles, "get_vehicle", fake_get_vehicle)

    response = auth_client.get(f"/api/v1/vehicles/{vehicle_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Vehicle not found."


def test_get_vehicle_forbidden(auth_client, monkeypatch):
    vehicle_id = uuid4()

    def fake_get_vehicle(db, vehicle_id, driver_id):
        raise VehicleForbiddenError(vehicle_id, driver_id)

    monkeypatch.setattr(vehicles, "get_vehicle", fake_get_vehicle)

    response = auth_client.get(f"/api/v1/vehicles/{vehicle_id}")

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You do not have permission to access or modify this vehicle."
    )


def test_get_vehicle_unauthenticated(client):
    app.dependency_overrides[get_db] = lambda: object()

    response = client.get(f"/api/v1/vehicles/{uuid4()}")

    assert response.status_code == 401


# =============================================================================
# PATCH /api/v1/vehicles/{vehicle_id}
# =============================================================================


def test_update_vehicle_success(auth_client, monkeypatch):
    vehicle_id = uuid4()
    fake_updated = make_fake_vehicle(
        vehicle_id=vehicle_id,
        driver_id=TEST_USER_ID,
        make="Honda",
        model="Civic",
        registration_number="KL-01-CD-5678",
        total_seats=5,
    )

    monkeypatch.setattr(
        vehicles,
        "update_vehicle",
        lambda db, vehicle_id, driver_id, payload: fake_updated,
    )

    response = auth_client.patch(
        f"/api/v1/vehicles/{vehicle_id}",
        json={"make": "Honda", "model": "Civic", "total_seats": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["make"] == "Honda"
    assert data["model"] == "Civic"
    assert data["total_seats"] == 5


def test_update_vehicle_not_found(auth_client, monkeypatch):
    vehicle_id = uuid4()

    def fake_update_vehicle(db, vehicle_id, driver_id, payload):
        raise VehicleNotFoundError(vehicle_id)

    monkeypatch.setattr(vehicles, "update_vehicle", fake_update_vehicle)

    response = auth_client.patch(
        f"/api/v1/vehicles/{vehicle_id}",
        json={"make": "Honda"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Vehicle not found."


def test_update_vehicle_forbidden(auth_client, monkeypatch):
    vehicle_id = uuid4()

    def fake_update_vehicle(db, vehicle_id, driver_id, payload):
        raise VehicleForbiddenError(vehicle_id, driver_id)

    monkeypatch.setattr(vehicles, "update_vehicle", fake_update_vehicle)

    response = auth_client.patch(
        f"/api/v1/vehicles/{vehicle_id}",
        json={"make": "Honda"},
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You do not have permission to access or modify this vehicle."
    )


def test_update_vehicle_duplicate_registration_returns_409(auth_client, monkeypatch):
    vehicle_id = uuid4()

    def fake_update_vehicle(db, vehicle_id, driver_id, payload):
        raise VehicleRegistrationAlreadyExistsError(payload.registration_number)

    monkeypatch.setattr(vehicles, "update_vehicle", fake_update_vehicle)

    response = auth_client.patch(
        f"/api/v1/vehicles/{vehicle_id}",
        json={"registration_number": "KL-01-CD-5678"},
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {"total_seats": 0},
        {"total_seats": -1},
        {"total_seats": 51},
        {"make": "   "},
        {"model": "   "},
        {"registration_number": "   "},
    ],
)
def test_update_vehicle_validation_error(auth_client, invalid_payload):
    vehicle_id = uuid4()
    response = auth_client.patch(
        f"/api/v1/vehicles/{vehicle_id}",
        json=invalid_payload,
    )

    assert response.status_code == 422


def test_update_vehicle_unauthenticated(client):
    app.dependency_overrides[get_db] = lambda: object()

    response = client.patch(
        f"/api/v1/vehicles/{uuid4()}",
        json={"make": "Honda"},
    )

    assert response.status_code == 401


# =============================================================================
# DELETE /api/v1/vehicles/{vehicle_id}
# =============================================================================


def test_delete_vehicle_success(auth_client, monkeypatch):
    vehicle_id = uuid4()
    deleted = {}

    def fake_delete_vehicle(db, vehicle_id, driver_id):
        deleted["called"] = True

    monkeypatch.setattr(vehicles, "delete_vehicle", fake_delete_vehicle)

    response = auth_client.delete(f"/api/v1/vehicles/{vehicle_id}")

    assert response.status_code == 204
    assert deleted["called"] is True


def test_delete_vehicle_not_found(auth_client, monkeypatch):
    vehicle_id = uuid4()

    def fake_delete_vehicle(db, vehicle_id, driver_id):
        raise VehicleNotFoundError(vehicle_id)

    monkeypatch.setattr(vehicles, "delete_vehicle", fake_delete_vehicle)

    response = auth_client.delete(f"/api/v1/vehicles/{vehicle_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Vehicle not found."


def test_delete_vehicle_forbidden(auth_client, monkeypatch):
    vehicle_id = uuid4()

    def fake_delete_vehicle(db, vehicle_id, driver_id):
        raise VehicleForbiddenError(vehicle_id, driver_id)

    monkeypatch.setattr(vehicles, "delete_vehicle", fake_delete_vehicle)

    response = auth_client.delete(f"/api/v1/vehicles/{vehicle_id}")

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You do not have permission to access or modify this vehicle."
    )
