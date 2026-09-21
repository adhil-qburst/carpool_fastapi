from datetime import datetime, time, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

import app.features.ride_preferences.services.create_ride_preference as create_pref_module
import app.features.ride_preferences.services.delete_ride_preference as delete_pref_module
import app.features.ride_preferences.services.get_ride_preference as get_pref_module
import app.features.ride_preferences.services.list_ride_preferences as list_pref_module
import app.features.ride_preferences.services.update_ride_preference as update_pref_module
from app.features.ride_preferences.exceptions import (
    DuplicateRidePreferenceError,
    InvalidRidePreferenceLabelError,
    InvalidSeatsNeededError,
    RidePreferenceForbiddenError,
    RidePreferenceNotFoundError,
    SameLocationRidePreferenceError,
)


class FakeSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def make_fake_preference(
    preference_id: UUID | None = None,
    rider_id: UUID | None = None,
    source_location_id: UUID | None = None,
    destination_location_id: UUID | None = None,
    preferred_departure_time: time | None = None,
    seats_needed: int = 1,
    is_active: bool = True,
    label: str | None = None,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=preference_id or uuid4(),
        rider_id=rider_id or uuid4(),
        source_location_id=source_location_id or uuid4(),
        destination_location_id=destination_location_id or uuid4(),
        preferred_departure_time=preferred_departure_time,
        seats_needed=seats_needed,
        is_active=is_active,
        label=label,
        created_at=now,
        updated_at=now,
    )


# =============================================================================
# create_ride_preference
# =============================================================================


def test_create_ride_preference_success(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    src_id = uuid4()
    dst_id = uuid4()

    created_fake = make_fake_preference(
        rider_id=rider_id,
        source_location_id=src_id,
        destination_location_id=dst_id,
        preferred_departure_time=time(9, 0),
        seats_needed=2,
        label="Work commute",
    )

    class FakeRepo:
        def get_active_by_rider_and_locations(self, s, *, rider_id, source_location_id, destination_location_id):
            return None

        def create(self, s, **kwargs):
            return created_fake

    monkeypatch.setattr(create_pref_module, "get_ride_preference_repo", lambda: FakeRepo())

    result = create_pref_module.create_ride_preference(
        session,
        rider_id=rider_id,
        source_location_id=src_id,
        destination_location_id=dst_id,
        preferred_departure_time=time(9, 0),
        seats_needed=2,
        label="  Work commute  ",
    )

    assert result == created_fake
    assert session.committed is True
    assert session.rolled_back is False


def test_create_ride_preference_same_locations(monkeypatch):
    session = FakeSession()
    loc_id = uuid4()

    with pytest.raises(SameLocationRidePreferenceError):
        create_pref_module.create_ride_preference(
            session,
            rider_id=uuid4(),
            source_location_id=loc_id,
            destination_location_id=loc_id,
        )


def test_create_ride_preference_invalid_seats(monkeypatch):
    session = FakeSession()

    with pytest.raises(InvalidSeatsNeededError):
        create_pref_module.create_ride_preference(
            session,
            rider_id=uuid4(),
            source_location_id=uuid4(),
            destination_location_id=uuid4(),
            seats_needed=0,
        )


def test_create_ride_preference_label_too_long(monkeypatch):
    session = FakeSession()

    with pytest.raises(InvalidRidePreferenceLabelError):
        create_pref_module.create_ride_preference(
            session,
            rider_id=uuid4(),
            source_location_id=uuid4(),
            destination_location_id=uuid4(),
            label="A" * 101,
        )


def test_create_ride_preference_duplicate(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    src_id = uuid4()
    dst_id = uuid4()

    existing = make_fake_preference(
        rider_id=rider_id,
        source_location_id=src_id,
        destination_location_id=dst_id,
    )

    class FakeRepo:
        def get_active_by_rider_and_locations(self, s, *, rider_id, source_location_id, destination_location_id):
            return existing

    monkeypatch.setattr(create_pref_module, "get_ride_preference_repo", lambda: FakeRepo())

    with pytest.raises(DuplicateRidePreferenceError):
        create_pref_module.create_ride_preference(
            session,
            rider_id=rider_id,
            source_location_id=src_id,
            destination_location_id=dst_id,
        )
    assert session.rolled_back is True


# =============================================================================
# get_ride_preference
# =============================================================================


def test_get_ride_preference_success(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    pref_id = uuid4()
    pref = make_fake_preference(preference_id=pref_id, rider_id=rider_id)

    class FakeRepo:
        def get_by_id_with_details(self, s, id_):
            return pref

    monkeypatch.setattr(get_pref_module, "get_ride_preference_repo", lambda: FakeRepo())

    result = get_pref_module.get_ride_preference(session, pref_id, rider_id, with_details=True)
    assert result == pref


def test_get_ride_preference_not_found(monkeypatch):
    session = FakeSession()
    pref_id = uuid4()
    rider_id = uuid4()

    class FakeRepo:
        def get_by_id_with_details(self, s, id_):
            return None

    monkeypatch.setattr(get_pref_module, "get_ride_preference_repo", lambda: FakeRepo())

    with pytest.raises(RidePreferenceNotFoundError):
        get_pref_module.get_ride_preference(session, pref_id, rider_id)


def test_get_ride_preference_forbidden(monkeypatch):
    session = FakeSession()
    pref_id = uuid4()
    owner_id = uuid4()
    intruder_id = uuid4()
    pref = make_fake_preference(preference_id=pref_id, rider_id=owner_id)

    class FakeRepo:
        def get_by_id_with_details(self, s, id_):
            return pref

    monkeypatch.setattr(get_pref_module, "get_ride_preference_repo", lambda: FakeRepo())

    with pytest.raises(RidePreferenceForbiddenError):
        get_pref_module.get_ride_preference(session, pref_id, intruder_id)


# =============================================================================
# list_ride_preferences
# =============================================================================


def test_list_user_ride_preferences(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    prefs = [make_fake_preference(rider_id=rider_id)]

    class FakeRepo:
        def list_by_rider_id(self, s, *, rider_id, active_only):
            return prefs

    monkeypatch.setattr(list_pref_module, "get_ride_preference_repo", lambda: FakeRepo())

    result = list_pref_module.list_user_ride_preferences(session, rider_id)
    assert result == prefs


def test_list_active_preferences_by_locations(monkeypatch):
    session = FakeSession()
    src_id = uuid4()
    dst_id = uuid4()
    prefs = [make_fake_preference(source_location_id=src_id, destination_location_id=dst_id)]

    class FakeRepo:
        def list_active_by_locations(self, s, *, source_location_id, destination_location_id):
            return prefs

    monkeypatch.setattr(list_pref_module, "get_ride_preference_repo", lambda: FakeRepo())

    result = list_pref_module.list_active_preferences_by_locations(
        session,
        source_location_id=src_id,
        destination_location_id=dst_id,
    )
    assert result == prefs


def test_list_active_preferences_same_locations(monkeypatch):
    session = FakeSession()
    loc_id = uuid4()

    with pytest.raises(SameLocationRidePreferenceError):
        list_pref_module.list_active_preferences_by_locations(
            session,
            source_location_id=loc_id,
            destination_location_id=loc_id,
        )


# =============================================================================
# update_ride_preference
# =============================================================================


def test_update_ride_preference_success(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    pref_id = uuid4()
    pref = make_fake_preference(preference_id=pref_id, rider_id=rider_id, seats_needed=1)

    class FakeRepo:
        def get_by_id_for_update(self, s, id_):
            return pref

        def get_active_by_rider_and_locations(self, s, *, rider_id, source_location_id, destination_location_id):
            return pref

        def update(self, s, p, **kwargs):
            p.seats_needed = kwargs.get("seats_needed", p.seats_needed)
            return p

    monkeypatch.setattr(update_pref_module, "get_ride_preference_repo", lambda: FakeRepo())

    result = update_pref_module.update_ride_preference(
        session,
        pref_id,
        rider_id,
        seats_needed=3,
    )

    assert result.seats_needed == 3
    assert session.committed is True
    assert session.rolled_back is False


def test_update_ride_preference_forbidden(monkeypatch):
    session = FakeSession()
    pref_id = uuid4()
    owner_id = uuid4()
    intruder_id = uuid4()
    pref = make_fake_preference(preference_id=pref_id, rider_id=owner_id)

    class FakeRepo:
        def get_by_id_for_update(self, s, id_):
            return pref

    monkeypatch.setattr(update_pref_module, "get_ride_preference_repo", lambda: FakeRepo())

    with pytest.raises(RidePreferenceForbiddenError):
        update_pref_module.update_ride_preference(
            session,
            pref_id,
            intruder_id,
            seats_needed=2,
        )
    assert session.rolled_back is True


# =============================================================================
# delete_ride_preference
# =============================================================================


def test_delete_ride_preference_success(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    pref_id = uuid4()
    pref = make_fake_preference(preference_id=pref_id, rider_id=rider_id)
    deleted = []

    class FakeRepo:
        def get_by_id_for_update(self, s, id_):
            return pref

        def delete(self, s, p):
            deleted.append(p)

    monkeypatch.setattr(delete_pref_module, "get_ride_preference_repo", lambda: FakeRepo())

    delete_pref_module.delete_ride_preference(session, pref_id, rider_id)

    assert len(deleted) == 1
    assert session.committed is True
    assert session.rolled_back is False


def test_delete_ride_preference_not_found(monkeypatch):
    session = FakeSession()
    pref_id = uuid4()
    rider_id = uuid4()

    class FakeRepo:
        def get_by_id_for_update(self, s, id_):
            return None

    monkeypatch.setattr(delete_pref_module, "get_ride_preference_repo", lambda: FakeRepo())

    with pytest.raises(RidePreferenceNotFoundError):
        delete_pref_module.delete_ride_preference(session, pref_id, rider_id)
    assert session.rolled_back is True
