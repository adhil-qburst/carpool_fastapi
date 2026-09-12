from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.db.session import get_db
from app.features.location.api import locations
from app.features.location.domain.enums import LocationStatus
from app.features.location.exceptions import (
    InvalidCoordinatesError,
    InvalidPaginationError,
)
from app.main import app


@pytest.fixture
def db_client(client):
    """Fixture providing TestClient with overridden DB dependency."""
    app.dependency_overrides[get_db] = lambda: object()
    yield client
    app.dependency_overrides.clear()


def make_fake_location(
    location_id: UUID | None = None,
    name: str = "Central Station",
    city: str = "Metropolis",
    lat: Decimal | float | None = Decimal("12.9716"),
    lng: Decimal | float | None = Decimal("77.5946"),
    status: LocationStatus = LocationStatus.ACTIVE,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=location_id or uuid4(),
        name=name,
        city=city,
        lat=Decimal(str(lat)) if lat is not None else None,
        lng=Decimal(str(lng)) if lng is not None else None,
        status=status,
        created_at=now,
        updated_at=now,
    )


# =============================================================================
# POST /api/v1/locations
# =============================================================================


def test_create_location_success(db_client, monkeypatch):
    location_id = uuid4()
    fake_location = make_fake_location(
        location_id=location_id,
        name="Central Station",
        city="Metropolis",
        lat=Decimal("12.9716"),
        lng=Decimal("77.5946"),
        status=LocationStatus.ACTIVE,
    )

    captured_call = {}

    def fake_create_location(session, **kwargs):
        captured_call.update(kwargs)
        return fake_location

    monkeypatch.setattr(locations, "create_location", fake_create_location)

    resp = db_client.post(
        "/api/v1/locations",
        json={
            "name": "Central Station",
            "city": "Metropolis",
            "lat": 12.9716,
            "lng": 77.5946,
            "status": "active",
        },
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == str(location_id)
    assert data["name"] == "Central Station"
    assert data["city"] == "Metropolis"
    assert Decimal(str(data["lat"])) == Decimal("12.9716")
    assert Decimal(str(data["lng"])) == Decimal("77.5946")
    assert data["status"] == "active"
    assert "created_at" in data
    assert "updated_at" in data

    assert captured_call["name"] == "Central Station"
    assert captured_call["city"] == "Metropolis"
    assert captured_call["status"] == LocationStatus.ACTIVE


def test_create_location_without_coordinates_success(db_client, monkeypatch):
    location_id = uuid4()
    fake_location = make_fake_location(
        location_id=location_id,
        name="North Park",
        city="Metropolis",
        lat=None,
        lng=None,
        status=LocationStatus.ACTIVE,
    )

    monkeypatch.setattr(
        locations, "create_location", lambda session, **kwargs: fake_location
    )

    resp = db_client.post(
        "/api/v1/locations",
        json={
            "name": "North Park",
            "city": "Metropolis",
        },
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == str(location_id)
    assert data["name"] == "North Park"
    assert data["city"] == "Metropolis"
    assert data["lat"] is None
    assert data["lng"] is None
    assert data["status"] == "active"


def test_create_location_invalid_coordinates_bad_request(db_client, monkeypatch):
    def fake_create_location(session, **kwargs):
        raise InvalidCoordinatesError(lat=100.0, lng=50.0)

    monkeypatch.setattr(locations, "create_location", fake_create_location)

    resp = db_client.post(
        "/api/v1/locations",
        json={
            "name": "Invalid Station",
            "city": "Metropolis",
            "lat": 10.0,
            "lng": 20.0,
        },
    )

    assert resp.status_code == 400
    assert "Invalid coordinates" in resp.json()["detail"]


def test_create_location_validation_error_missing_required_fields(db_client):
    resp = db_client.post(
        "/api/v1/locations",
        json={},
    )
    assert resp.status_code == 422


def test_create_location_validation_error_blank_name_or_city(db_client):
    resp = db_client.post(
        "/api/v1/locations",
        json={
            "name": "   ",
            "city": "   ",
        },
    )
    assert resp.status_code == 422


def test_create_location_validation_error_coordinate_out_of_range(db_client):
    resp = db_client.post(
        "/api/v1/locations",
        json={
            "name": "Central Station",
            "city": "Metropolis",
            "lat": 95.0,
            "lng": 50.0,
        },
    )
    assert resp.status_code == 422


def test_create_location_validation_error_invalid_status(db_client):
    resp = db_client.post(
        "/api/v1/locations",
        json={
            "name": "Central Station",
            "city": "Metropolis",
            "status": "unknown_status",
        },
    )
    assert resp.status_code == 422


# =============================================================================
# GET /api/v1/locations
# =============================================================================


def test_search_locations_default_params_success(db_client, monkeypatch):
    fake_loc = make_fake_location(name="Central Station")
    captured_call = {}

    def fake_search_locations(session, **kwargs):
        captured_call.update(kwargs)
        return [fake_loc], 1

    monkeypatch.setattr(locations, "search_locations", fake_search_locations)

    resp = db_client.get("/api/v1/locations")

    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Central Station"

    assert captured_call["text"] == ""
    assert captured_call["limit"] == 20
    assert captured_call["offset"] == 0
    assert captured_call["status"] == LocationStatus.ACTIVE


def test_search_locations_custom_params_success(db_client, monkeypatch):
    fake_loc = make_fake_location(name="Downtown Hub")
    captured_call = {}

    def fake_search_locations(session, **kwargs):
        captured_call.update(kwargs)
        return [fake_loc], 25

    monkeypatch.setattr(locations, "search_locations", fake_search_locations)

    resp = db_client.get(
        "/api/v1/locations",
        params={
            "search": "Downtown",
            "page": 3,
            "limit": 10,
            "status": "active",
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 3
    assert data["limit"] == 10
    assert data["total"] == 25
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Downtown Hub"

    assert captured_call["text"] == "Downtown"
    assert captured_call["limit"] == 10
    assert captured_call["offset"] == 20  # (page - 1) * limit = (3 - 1) * 10
    assert captured_call["status"] == LocationStatus.ACTIVE


def test_search_locations_empty_result_success(db_client, monkeypatch):
    monkeypatch.setattr(
        locations, "search_locations", lambda session, **kwargs: ([], 0)
    )

    resp = db_client.get("/api/v1/locations", params={"search": "NonExistent"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["total"] == 0
    assert data["items"] == []


def test_search_locations_invalid_pagination_bad_request(db_client, monkeypatch):
    def fake_search_locations(session, **kwargs):
        raise InvalidPaginationError(limit=0, offset=-1)

    monkeypatch.setattr(locations, "search_locations", fake_search_locations)

    resp = db_client.get("/api/v1/locations")

    assert resp.status_code == 400
    assert (
        resp.json()["detail"]
        == "Limit must be greater than 0 and offset must be non-negative."
    )


def test_search_locations_validation_error_invalid_page(db_client):
    resp = db_client.get("/api/v1/locations", params={"page": 0})
    assert resp.status_code == 422


def test_search_locations_validation_error_limit_out_of_range(db_client):
    resp_zero = db_client.get("/api/v1/locations", params={"limit": 0})
    assert resp_zero.status_code == 422

    resp_too_high = db_client.get("/api/v1/locations", params={"limit": 101})
    assert resp_too_high.status_code == 422


def test_search_locations_validation_error_invalid_status(db_client):
    resp = db_client.get("/api/v1/locations", params={"status": "invalid_val"})
    assert resp.status_code == 422
