from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

import app.features.location.services.create_location as create_location_service
import app.features.location.services.delete_location as delete_location_service
import app.features.location.services.get_location as get_location_service
import app.features.location.services.search_locations as search_locations_service
import app.features.location.services.update_location as update_location_service
from app.features.location.domain.enums import LocationStatus
from app.features.location.exceptions import (
    InvalidCoordinatesError,
    InvalidPaginationError,
    LocationNotFoundError,
)


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def make_fake_location(
    location_id: UUID | None = None,
    name: str = "Central Station",
    city: str = "Kozhikode",
    lat: Decimal | None = Decimal("11.2588"),
    lng: Decimal | None = Decimal("75.7804"),
    status: LocationStatus = LocationStatus.ACTIVE,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=location_id or uuid4(),
        name=name,
        city=city,
        lat=lat,
        lng=lng,
        status=status,
        created_at=now,
        updated_at=now,
    )


# =============================================================================
# create_location
# =============================================================================


def test_create_location_success(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    fake_loc = make_fake_location(
        name="Central Bus Station",
        city="Kozhikode",
        lat=Decimal("11.25"),
        lng=Decimal("75.78"),
    )

    class FakeLocationRepo:
        def create(
            self,
            s,
            *,
            name,
            city,
            lat=None,
            lng=None,
            status=LocationStatus.ACTIVE,
        ):
            assert s is session
            assert name == "Central Bus Station"
            assert city == "Kozhikode"
            assert lat == Decimal("11.25")
            assert lng == Decimal("75.78")
            assert status == LocationStatus.ACTIVE
            return fake_loc

    monkeypatch.setattr(
        create_location_service,
        "get_location_repo",
        lambda: FakeLocationRepo(),
    )

    result = create_location_service.create_location(
        session,  # type: ignore[arg-type]
        name="  Central Bus Station  ",
        city="  Kozhikode  ",
        lat=Decimal("11.25"),
        lng=Decimal("75.78"),
    )

    assert result == fake_loc
    assert session.committed is True
    assert session.rolled_back is False


def test_create_location_invalid_coordinates() -> None:
    session = FakeSession()

    with pytest.raises(InvalidCoordinatesError):
        create_location_service.create_location(
            session,  # type: ignore[arg-type]
            name="Somewhere",
            city="Nowhere",
            lat=Decimal("95.0"),  # > 90
            lng=Decimal("75.0"),
        )

    with pytest.raises(InvalidCoordinatesError):
        create_location_service.create_location(
            session,  # type: ignore[arg-type]
            name="Somewhere",
            city="Nowhere",
            lat=Decimal("11.0"),
            lng=None,  # only one coordinate provided
        )

    assert session.committed is False


def test_create_location_rollback_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    class FailingRepo:
        def create(self, *args, **kwargs):
            raise RuntimeError("Database error")

    monkeypatch.setattr(
        create_location_service, "get_location_repo", lambda: FailingRepo()
    )

    with pytest.raises(RuntimeError, match="Database error"):
        create_location_service.create_location(
            session,  # type: ignore[arg-type]
            name="Station",
            city="City",
        )

    assert session.committed is False
    assert session.rolled_back is True


# =============================================================================
# get_location
# =============================================================================


def test_get_location_success(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    loc_id = uuid4()
    fake_loc = make_fake_location(location_id=loc_id)

    class FakeLocationRepo:
        def get_by_id(self, s, target_id):
            assert s is session
            assert target_id == loc_id
            return fake_loc

    monkeypatch.setattr(
        get_location_service, "get_location_repo", lambda: FakeLocationRepo()
    )

    result = get_location_service.get_location(session, loc_id)  # type: ignore[arg-type]
    assert result == fake_loc


def test_get_location_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    loc_id = uuid4()

    class FakeLocationRepo:
        def get_by_id(self, s, target_id):
            return None

    monkeypatch.setattr(
        get_location_service, "get_location_repo", lambda: FakeLocationRepo()
    )

    with pytest.raises(LocationNotFoundError) as exc_info:
        get_location_service.get_location(session, loc_id)  # type: ignore[arg-type]

    assert exc_info.value.location_id == loc_id
    assert exc_info.value.code == "LOCATION_NOT_FOUND"


# =============================================================================
# search_locations
# =============================================================================


def test_search_locations_success(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    fake_loc = make_fake_location()

    class FakeLocationRepo:
        def search(self, s, *, text, limit, offset, status):
            assert s is session
            assert text == "Station"
            assert limit == 10
            assert offset == 0
            assert status == LocationStatus.ACTIVE
            return [fake_loc]

        def count_search(self, s, *, text, status):
            assert s is session
            assert text == "Station"
            assert status == LocationStatus.ACTIVE
            return 1

    monkeypatch.setattr(
        search_locations_service,
        "get_location_repo",
        lambda: FakeLocationRepo(),
    )

    items, total = search_locations_service.search_locations(
        session,  # type: ignore[arg-type]
        text="  Station  ",
        limit=10,
        offset=0,
    )

    assert items == [fake_loc]
    assert total == 1


def test_search_locations_invalid_pagination() -> None:
    session = FakeSession()

    with pytest.raises(InvalidPaginationError):
        search_locations_service.search_locations(
            session,  # type: ignore[arg-type]
            limit=0,
            offset=0,
        )

    with pytest.raises(InvalidPaginationError):
        search_locations_service.search_locations(
            session,  # type: ignore[arg-type]
            limit=10,
            offset=-1,
        )


# =============================================================================
# update_location
# =============================================================================


def test_update_location_success(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    loc_id = uuid4()
    existing_loc = make_fake_location(
        location_id=loc_id,
        name="Old Name",
        city="Old City",
        lat=Decimal("10.0"),
        lng=Decimal("70.0"),
    )

    class FakeLocationRepo:
        def get_by_id_for_update(self, s, target_id):
            assert target_id == loc_id
            return existing_loc

        def update(self, s, loc, *, name, city, lat, lng, status):
            assert loc is existing_loc
            assert name == "New Name"
            assert city == "New City"
            assert lat == Decimal("11.5")
            assert lng == Decimal("76.0")
            assert status == LocationStatus.INACTIVE
            loc.name = name
            loc.city = city
            loc.lat = lat
            loc.lng = lng
            loc.status = status
            return loc

    monkeypatch.setattr(
        update_location_service,
        "get_location_repo",
        lambda: FakeLocationRepo(),
    )

    updated = update_location_service.update_location(
        session,  # type: ignore[arg-type]
        loc_id,
        name="  New Name  ",
        city="  New City  ",
        lat=Decimal("11.5"),
        lng=Decimal("76.0"),
        status=LocationStatus.INACTIVE,
    )

    assert updated.name == "New Name"
    assert updated.city == "New City"
    assert updated.status == LocationStatus.INACTIVE
    assert session.committed is True
    assert session.rolled_back is False


def test_update_location_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    loc_id = uuid4()

    class FakeLocationRepo:
        def get_by_id_for_update(self, s, target_id):
            return None

    monkeypatch.setattr(
        update_location_service,
        "get_location_repo",
        lambda: FakeLocationRepo(),
    )

    with pytest.raises(LocationNotFoundError):
        update_location_service.update_location(
            session,  # type: ignore[arg-type]
            loc_id,
            name="New Name",
        )

    assert session.committed is False


def test_update_location_invalid_coordinates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    loc_id = uuid4()
    existing_loc = make_fake_location(location_id=loc_id)

    class FakeLocationRepo:
        def get_by_id_for_update(self, s, target_id):
            return existing_loc

    monkeypatch.setattr(
        update_location_service,
        "get_location_repo",
        lambda: FakeLocationRepo(),
    )

    with pytest.raises(InvalidCoordinatesError):
        update_location_service.update_location(
            session,  # type: ignore[arg-type]
            loc_id,
            lat=Decimal("120.0"),  # Out of range
        )

    assert session.committed is False


def test_update_location_rollback_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    loc_id = uuid4()
    existing_loc = make_fake_location(location_id=loc_id)

    class FailingRepo:
        def get_by_id_for_update(self, s, target_id):
            return existing_loc

        def update(self, *args, **kwargs):
            raise RuntimeError("Update failed")

    monkeypatch.setattr(
        update_location_service,
        "get_location_repo",
        lambda: FailingRepo(),
    )

    with pytest.raises(RuntimeError, match="Update failed"):
        update_location_service.update_location(
            session,  # type: ignore[arg-type]
            loc_id,
            name="New",
        )

    assert session.committed is False
    assert session.rolled_back is True


# =============================================================================
# delete_location
# =============================================================================


def test_delete_location_success(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    loc_id = uuid4()
    existing_loc = make_fake_location(location_id=loc_id)
    deleted = False

    class FakeLocationRepo:
        def get_by_id_for_update(self, s, target_id):
            assert target_id == loc_id
            return existing_loc

        def delete(self, s, loc):
            nonlocal deleted
            assert loc is existing_loc
            deleted = True

    monkeypatch.setattr(
        delete_location_service,
        "get_location_repo",
        lambda: FakeLocationRepo(),
    )

    delete_location_service.delete_location(session, loc_id)  # type: ignore[arg-type]

    assert deleted is True
    assert session.committed is True
    assert session.rolled_back is False


def test_delete_location_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    loc_id = uuid4()

    class FakeLocationRepo:
        def get_by_id_for_update(self, s, target_id):
            return None

    monkeypatch.setattr(
        delete_location_service,
        "get_location_repo",
        lambda: FakeLocationRepo(),
    )

    with pytest.raises(LocationNotFoundError):
        delete_location_service.delete_location(session, loc_id)  # type: ignore[arg-type]

    assert session.committed is False


def test_delete_location_rollback_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    loc_id = uuid4()
    existing_loc = make_fake_location(location_id=loc_id)

    class FailingRepo:
        def get_by_id_for_update(self, s, target_id):
            return existing_loc

        def delete(self, *args, **kwargs):
            raise RuntimeError("Delete failed")

    monkeypatch.setattr(
        delete_location_service,
        "get_location_repo",
        lambda: FailingRepo(),
    )

    with pytest.raises(RuntimeError, match="Delete failed"):
        delete_location_service.delete_location(session, loc_id)  # type: ignore[arg-type]

    assert session.committed is False
    assert session.rolled_back is True
