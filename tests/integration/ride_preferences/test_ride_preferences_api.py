from datetime import datetime, time, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.ride_preferences.api import ride_preferences
from app.features.ride_preferences.exceptions import (
    DuplicateRidePreferenceError,
    InvalidRidePreferenceLabelError,
    InvalidSeatsNeededError,
    RidePreferenceForbiddenError,
    RidePreferenceNotFoundError,
    SameLocationRidePreferenceError,
)
from app.main import app

TEST_USER_ID = UUID("11111111-1111-1111-1111-111111111111")
SOURCE_ID = UUID("22222222-2222-2222-2222-222222222222")
DEST_ID = UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
def auth_client(client):
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    yield client
    app.dependency_overrides.clear()


def make_fake_preference(
    preference_id: UUID | None = None,
    rider_id: UUID | None = None,
    source_location_id: UUID | None = None,
    destination_location_id: UUID | None = None,
    preferred_departure_time: time | None = time(8, 30),
    seats_needed: int = 1,
    is_active: bool = True,
    label: str | None = "Morning Commute",
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=preference_id or uuid4(),
        rider_id=rider_id or TEST_USER_ID,
        source_location_id=source_location_id or SOURCE_ID,
        destination_location_id=destination_location_id or DEST_ID,
        preferred_departure_time=preferred_departure_time,
        seats_needed=seats_needed,
        is_active=is_active,
        label=label,
        created_at=now,
        updated_at=now,
        source=None,
        destination=None,
        rider=None,
    )


# =============================================================================
# POST /api/v1/ride-preferences
# =============================================================================


def test_create_ride_preference_success(auth_client, monkeypatch):
    pref_id = uuid4()
    fake = make_fake_preference(preference_id=pref_id)
    monkeypatch.setattr(ride_preferences, "create_ride_preference", lambda **kwargs: fake)

    resp = auth_client.post(
        "/api/v1/ride-preferences",
        json={
            "source_location_id": str(SOURCE_ID),
            "destination_location_id": str(DEST_ID),
            "preferred_departure_time": "08:30:00",
            "seats_needed": 1,
            "is_active": True,
            "label": "Morning Commute",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == str(pref_id)
    assert data["rider_id"] == str(TEST_USER_ID)
    assert data["seats_needed"] == 1
    assert data["label"] == "Morning Commute"


def test_create_ride_preference_same_location(auth_client, monkeypatch):
    def fake_create(**kwargs):
        raise SameLocationRidePreferenceError()

    monkeypatch.setattr(ride_preferences, "create_ride_preference", fake_create)

    resp = auth_client.post(
        "/api/v1/ride-preferences",
        json={
            "source_location_id": str(SOURCE_ID),
            "destination_location_id": str(SOURCE_ID),
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Source and destination locations must be different."


def test_create_ride_preference_duplicate(auth_client, monkeypatch):
    def fake_create(**kwargs):
        raise DuplicateRidePreferenceError()

    monkeypatch.setattr(ride_preferences, "create_ride_preference", fake_create)

    resp = auth_client.post(
        "/api/v1/ride-preferences",
        json={
            "source_location_id": str(SOURCE_ID),
            "destination_location_id": str(DEST_ID),
        },
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "An active ride preference between these locations already exists."


# =============================================================================
# GET /api/v1/ride-preferences
# =============================================================================


def test_list_ride_preferences_success(auth_client, monkeypatch):
    p1 = make_fake_preference()
    p2 = make_fake_preference()
    monkeypatch.setattr(ride_preferences, "list_user_ride_preferences", lambda **kwargs: [p1, p2])

    resp = auth_client.get("/api/v1/ride-preferences?active_only=true")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


# =============================================================================
# GET /api/v1/ride-preferences/matches
# =============================================================================


def test_list_matching_preferences_success(auth_client, monkeypatch):
    p1 = make_fake_preference()
    monkeypatch.setattr(ride_preferences, "list_active_preferences_by_locations", lambda **kwargs: [p1])

    resp = auth_client.get(
        f"/api/v1/ride-preferences/matches?source_location_id={SOURCE_ID}&destination_location_id={DEST_ID}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == str(p1.id)


def test_list_matching_preferences_same_location(auth_client, monkeypatch):
    def fake_list(**kwargs):
        raise SameLocationRidePreferenceError()

    monkeypatch.setattr(ride_preferences, "list_active_preferences_by_locations", fake_list)

    resp = auth_client.get(
        f"/api/v1/ride-preferences/matches?source_location_id={SOURCE_ID}&destination_location_id={SOURCE_ID}"
    )
    assert resp.status_code == 400


# =============================================================================
# GET /api/v1/ride-preferences/{preference_id}
# =============================================================================


def test_get_ride_preference_success(auth_client, monkeypatch):
    pref_id = uuid4()
    fake = make_fake_preference(preference_id=pref_id)
    monkeypatch.setattr(ride_preferences, "get_ride_preference", lambda **kwargs: fake)

    resp = auth_client.get(f"/api/v1/ride-preferences/{pref_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(pref_id)


def test_get_ride_preference_not_found(auth_client, monkeypatch):
    pref_id = uuid4()

    def fake_get(**kwargs):
        raise RidePreferenceNotFoundError(preference_id=pref_id)

    monkeypatch.setattr(ride_preferences, "get_ride_preference", fake_get)

    resp = auth_client.get(f"/api/v1/ride-preferences/{pref_id}")
    assert resp.status_code == 404


def test_get_ride_preference_forbidden(auth_client, monkeypatch):
    pref_id = uuid4()

    def fake_get(**kwargs):
        raise RidePreferenceForbiddenError()

    monkeypatch.setattr(ride_preferences, "get_ride_preference", fake_get)

    resp = auth_client.get(f"/api/v1/ride-preferences/{pref_id}")
    assert resp.status_code == 403


# =============================================================================
# PATCH /api/v1/ride-preferences/{preference_id}
# =============================================================================


def test_update_ride_preference_success(auth_client, monkeypatch):
    pref_id = uuid4()
    fake = make_fake_preference(preference_id=pref_id, label="Updated Label")
    monkeypatch.setattr(ride_preferences, "update_ride_preference", lambda **kwargs: fake)

    resp = auth_client.patch(
        f"/api/v1/ride-preferences/{pref_id}",
        json={"label": "Updated Label"},
    )
    assert resp.status_code == 200
    assert resp.json()["label"] == "Updated Label"


def test_update_ride_preference_not_found(auth_client, monkeypatch):
    pref_id = uuid4()

    def fake_update(**kwargs):
        raise RidePreferenceNotFoundError()

    monkeypatch.setattr(ride_preferences, "update_ride_preference", fake_update)

    resp = auth_client.patch(
        f"/api/v1/ride-preferences/{pref_id}",
        json={"seats_needed": 2},
    )
    assert resp.status_code == 404


# =============================================================================
# DELETE /api/v1/ride-preferences/{preference_id}
# =============================================================================


def test_delete_ride_preference_success(auth_client, monkeypatch):
    pref_id = uuid4()
    monkeypatch.setattr(ride_preferences, "delete_ride_preference", lambda **kwargs: None)

    resp = auth_client.delete(f"/api/v1/ride-preferences/{pref_id}")
    assert resp.status_code == 204


def test_delete_ride_preference_not_found(auth_client, monkeypatch):
    pref_id = uuid4()

    def fake_delete(**kwargs):
        raise RidePreferenceNotFoundError()

    monkeypatch.setattr(ride_preferences, "delete_ride_preference", fake_delete)

    resp = auth_client.delete(f"/api/v1/ride-preferences/{pref_id}")
    assert resp.status_code == 404
