from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.features.vehicles.exceptions import (
    VehicleForbiddenError,
    VehicleNotFoundError,
    VehicleRegistrationAlreadyExistsError,
)
from app.features.vehicles.schemas.create_vehicle import CreateVehicleRequest
from app.features.vehicles.schemas.update_vehicle import UpdateVehicleRequest
import app.features.vehicles.services.create_vehicle as create_vehicle_service
import app.features.vehicles.services.delete_vehicle as delete_vehicle_service
import app.features.vehicles.services.get_vehicle as get_vehicle_service
import app.features.vehicles.services.list_vehicles as list_vehicles_service
import app.features.vehicles.services.update_vehicle as update_vehicle_service


class FakeSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


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
        driver_id=driver_id or uuid4(),
        make=make,
        model=model,
        registration_number=registration_number,
        total_seats=total_seats,
        created_at=now,
        updated_at=now,
    )


# =============================================================================
# create_vehicle
# =============================================================================


def test_create_vehicle_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    payload = CreateVehicleRequest(
        make="Toyota",
        model="Prius",
        registration_number="kl-01-ab-1234",
        total_seats=4,
    )
    fake_created = make_fake_vehicle(
        driver_id=driver_id,
        make="Toyota",
        model="Prius",
        registration_number="KL-01-AB-1234",
        total_seats=4,
    )
    captured = {}

    def fake_create(s, **kwargs):
        captured["session"] = s
        captured.update(kwargs)
        return fake_created

    fake_repo = SimpleNamespace(
        get_by_registration_number=lambda s, reg: None,
        create=fake_create,
    )
    monkeypatch.setattr(create_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    result = create_vehicle_service.create_vehicle(session, driver_id, payload)

    assert result == fake_created
    assert session.committed is True
    assert session.rolled_back is False
    assert captured["driver_id"] == driver_id
    assert captured["registration_number"] == "KL-01-AB-1234"
    assert captured["make"] == "Toyota"
    assert captured["model"] == "Prius"
    assert captured["total_seats"] == 4


def test_create_vehicle_duplicate_registration_raises_error(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    payload = CreateVehicleRequest(
        make="Toyota",
        model="Prius",
        registration_number="KL-01-AB-1234",
        total_seats=4,
    )
    existing_vehicle = make_fake_vehicle(
        registration_number="KL-01-AB-1234",
    )
    fake_repo = SimpleNamespace(
        get_by_registration_number=lambda s, reg: existing_vehicle,
    )
    monkeypatch.setattr(create_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    with pytest.raises(VehicleRegistrationAlreadyExistsError) as exc_info:
        create_vehicle_service.create_vehicle(session, driver_id, payload)

    assert exc_info.value.registration_number == "KL-01-AB-1234"
    assert session.committed is False
    assert session.rolled_back is True


# =============================================================================
# get_vehicle
# =============================================================================


def test_get_vehicle_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    vehicle_id = uuid4()
    fake_vehicle = make_fake_vehicle(vehicle_id=vehicle_id, driver_id=driver_id)

    fake_repo = SimpleNamespace(
        get_by_id=lambda s, v_id: fake_vehicle if v_id == vehicle_id else None,
    )
    monkeypatch.setattr(get_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    result = get_vehicle_service.get_vehicle(session, vehicle_id, driver_id)

    assert result == fake_vehicle


def test_get_vehicle_not_found_raises_error(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    vehicle_id = uuid4()

    fake_repo = SimpleNamespace(
        get_by_id=lambda s, v_id: None,
    )
    monkeypatch.setattr(get_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    with pytest.raises(VehicleNotFoundError) as exc_info:
        get_vehicle_service.get_vehicle(session, vehicle_id, driver_id)

    assert exc_info.value.vehicle_id == vehicle_id


def test_get_vehicle_forbidden_raises_error(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    other_driver_id = uuid4()
    vehicle_id = uuid4()
    fake_vehicle = make_fake_vehicle(vehicle_id=vehicle_id, driver_id=other_driver_id)

    fake_repo = SimpleNamespace(
        get_by_id=lambda s, v_id: fake_vehicle,
    )
    monkeypatch.setattr(get_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    with pytest.raises(VehicleForbiddenError) as exc_info:
        get_vehicle_service.get_vehicle(session, vehicle_id, driver_id)

    assert exc_info.value.vehicle_id == vehicle_id
    assert exc_info.value.user_id == driver_id


# =============================================================================
# update_vehicle
# =============================================================================


def test_update_vehicle_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    vehicle_id = uuid4()
    existing_vehicle = make_fake_vehicle(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        make="Toyota",
        model="Prius",
        registration_number="KL-01-AB-1234",
        total_seats=4,
    )
    updated_vehicle = make_fake_vehicle(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        make="Honda",
        model="Civic",
        registration_number="KL-01-CD-5678",
        total_seats=5,
    )
    payload = UpdateVehicleRequest(
        make="Honda",
        model="Civic",
        registration_number="kl-01-cd-5678",
        total_seats=5,
    )
    captured = {}

    def fake_update(s, v, **kwargs):
        captured["session"] = s
        captured["vehicle"] = v
        captured.update(kwargs)
        return updated_vehicle

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, v_id: existing_vehicle,
        get_by_registration_number=lambda s, reg: None,
        update=fake_update,
    )
    monkeypatch.setattr(update_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    result = update_vehicle_service.update_vehicle(
        session, vehicle_id, driver_id, payload
    )

    assert result == updated_vehicle
    assert session.committed is True
    assert session.rolled_back is False
    assert captured["make"] == "Honda"
    assert captured["model"] == "Civic"
    assert captured["registration_number"] == "KL-01-CD-5678"
    assert captured["total_seats"] == 5


def test_update_vehicle_not_found_raises_error(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    vehicle_id = uuid4()
    payload = UpdateVehicleRequest(make="Honda")

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, v_id: None,
    )
    monkeypatch.setattr(update_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    with pytest.raises(VehicleNotFoundError) as exc_info:
        update_vehicle_service.update_vehicle(session, vehicle_id, driver_id, payload)

    assert exc_info.value.vehicle_id == vehicle_id
    assert session.committed is False
    assert session.rolled_back is True


def test_update_vehicle_forbidden_raises_error(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    other_driver_id = uuid4()
    vehicle_id = uuid4()
    existing_vehicle = make_fake_vehicle(
        vehicle_id=vehicle_id,
        driver_id=other_driver_id,
    )
    payload = UpdateVehicleRequest(make="Honda")

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, v_id: existing_vehicle,
    )
    monkeypatch.setattr(update_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    with pytest.raises(VehicleForbiddenError) as exc_info:
        update_vehicle_service.update_vehicle(session, vehicle_id, driver_id, payload)

    assert exc_info.value.vehicle_id == vehicle_id
    assert exc_info.value.user_id == driver_id
    assert session.committed is False
    assert session.rolled_back is True


def test_update_vehicle_duplicate_registration_raises_error(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    vehicle_id = uuid4()
    other_vehicle_id = uuid4()
    existing_vehicle = make_fake_vehicle(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        registration_number="KL-01-AB-1234",
    )
    conflicting_vehicle = make_fake_vehicle(
        vehicle_id=other_vehicle_id,
        registration_number="KL-01-CD-5678",
    )
    payload = UpdateVehicleRequest(registration_number="KL-01-CD-5678")

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, v_id: existing_vehicle,
        get_by_registration_number=lambda s, reg: conflicting_vehicle,
    )
    monkeypatch.setattr(update_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    with pytest.raises(VehicleRegistrationAlreadyExistsError) as exc_info:
        update_vehicle_service.update_vehicle(session, vehicle_id, driver_id, payload)

    assert exc_info.value.registration_number == "KL-01-CD-5678"
    assert session.committed is False
    assert session.rolled_back is True


def test_update_vehicle_same_registration_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    vehicle_id = uuid4()
    existing_vehicle = make_fake_vehicle(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        registration_number="KL-01-AB-1234",
    )
    payload = UpdateVehicleRequest(registration_number="kl-01-ab-1234")

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, v_id: existing_vehicle,
        get_by_registration_number=lambda s, reg: existing_vehicle,
        update=lambda s, v, **kwargs: existing_vehicle,
    )
    monkeypatch.setattr(update_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    result = update_vehicle_service.update_vehicle(
        session, vehicle_id, driver_id, payload
    )

    assert result == existing_vehicle
    assert session.committed is True
    assert session.rolled_back is False


# =============================================================================
# delete_vehicle
# =============================================================================


def test_delete_vehicle_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    vehicle_id = uuid4()
    existing_vehicle = make_fake_vehicle(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
    )
    deleted = {}

    def fake_delete(s, v):
        deleted["vehicle"] = v

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, v_id: existing_vehicle,
        delete=fake_delete,
    )
    monkeypatch.setattr(delete_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    delete_vehicle_service.delete_vehicle(session, vehicle_id, driver_id)

    assert deleted["vehicle"] == existing_vehicle
    assert session.committed is True
    assert session.rolled_back is False


def test_delete_vehicle_not_found_raises_error(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    vehicle_id = uuid4()

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, v_id: None,
    )
    monkeypatch.setattr(delete_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    with pytest.raises(VehicleNotFoundError) as exc_info:
        delete_vehicle_service.delete_vehicle(session, vehicle_id, driver_id)

    assert exc_info.value.vehicle_id == vehicle_id
    assert session.committed is False
    assert session.rolled_back is True


def test_delete_vehicle_forbidden_raises_error(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    other_driver_id = uuid4()
    vehicle_id = uuid4()
    existing_vehicle = make_fake_vehicle(
        vehicle_id=vehicle_id,
        driver_id=other_driver_id,
    )

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, v_id: existing_vehicle,
    )
    monkeypatch.setattr(delete_vehicle_service, "get_vehicle_repo", lambda: fake_repo)

    with pytest.raises(VehicleForbiddenError) as exc_info:
        delete_vehicle_service.delete_vehicle(session, vehicle_id, driver_id)

    assert exc_info.value.vehicle_id == vehicle_id
    assert exc_info.value.user_id == driver_id
    assert session.committed is False
    assert session.rolled_back is True


# =============================================================================
# list_user_vehicles
# =============================================================================


def test_list_user_vehicles_returns_driver_vehicles(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    vehicles = [
        make_fake_vehicle(driver_id=driver_id, make="Toyota"),
        make_fake_vehicle(driver_id=driver_id, make="Honda"),
    ]

    fake_repo = SimpleNamespace(
        list_by_driver_id=lambda s, driver_id: vehicles if driver_id == driver_id else [],
    )
    monkeypatch.setattr(list_vehicles_service, "get_vehicle_repo", lambda: fake_repo)

    result = list_vehicles_service.list_user_vehicles(session, driver_id)

    assert result == vehicles
    assert len(result) == 2
