from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

import app.features.trips.services.create_trip as create_trip_service
import app.features.trips.services.delete_trip as delete_trip_service
import app.features.trips.services.get_trip as get_trip_service
import app.features.trips.services.list_trips as list_trips_service
import app.features.trips.services.search_trips as search_trips_service
import app.features.trips.services.update_trip as update_trip_service
from app.features.routes.domain.enums import RouteStatus
from app.features.trips.domain.enums import TripStatus
from app.features.trips.exceptions import (
    IdenticalSourceDestinationError,
    InvalidAvailableSeatsError,
    InvalidPaginationError,
    PastDepartureError,
    RouteForbiddenError,
    RouteNotActiveError,
    RouteNotFoundError,
    TripCannotBeDeletedError,
    TripCannotBeModifiedError,
    TripForbiddenError,
    TripNotFoundError,
)
from app.features.trips.schemas.create_trip import CreateTripRequest
from app.features.trips.schemas.update_trip import UpdateTripRequest


class FakeSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


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
        driver_id=driver_id or uuid4(),
        vehicle_id=vehicle_id or uuid4(),
        departure_date=departure_date or future_date,
        departure_time=departure_time or time(10, 0),
        available_seats=available_seats,
        status=status,
        created_at=now,
        updated_at=now,
    )


# =============================================================================
# create_trip
# =============================================================================


def test_create_trip_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    route_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=2)

    fake_route = SimpleNamespace(
        id=route_id,
        driver_id=driver_id,
        status=RouteStatus.ACTIVE,
    )
    fake_route_repo = SimpleNamespace(get_by_id=lambda s, rid: fake_route)
    monkeypatch.setattr(create_trip_service, "get_route_repo", lambda: fake_route_repo)

    fake_vehicle = SimpleNamespace(
        id=vehicle_id,
        driver_id=driver_id,
        total_seats=5,
    )
    fake_vehicle_repo = SimpleNamespace(get_by_id=lambda s, vid: fake_vehicle)
    monkeypatch.setattr(create_trip_service, "get_vehicle_repo", lambda: fake_vehicle_repo)

    payload = CreateTripRequest(
        route_id=route_id,
        vehicle_id=vehicle_id,
        departure_date=future_date,
        departure_time=time(14, 30),
    )

    fake_created = make_fake_trip(
        route_id=route_id,
        driver_id=driver_id,
        vehicle_id=vehicle_id,
        departure_date=future_date,
        departure_time=time(14, 30),
        available_seats=4,
    )
    captured = {}

    def fake_create(s, **kwargs):
        captured["session"] = s
        captured.update(kwargs)
        return fake_created

    fake_trip_repo = SimpleNamespace(create=fake_create)
    monkeypatch.setattr(create_trip_service, "get_trip_repo", lambda: fake_trip_repo)

    result = create_trip_service.create_trip(session, driver_id=driver_id, payload=payload)

    assert result == fake_created
    assert session.committed is True
    assert session.rolled_back is False
    assert captured["route_id"] == route_id
    assert captured["driver_id"] == driver_id
    assert captured["vehicle_id"] == vehicle_id
    assert captured["departure_date"] == future_date
    assert captured["departure_time"] == time(14, 30)
    assert captured["available_seats"] == 4


def test_create_trip_route_not_found(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    route_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=2)

    fake_route_repo = SimpleNamespace(get_by_id=lambda s, rid: None)
    monkeypatch.setattr(create_trip_service, "get_route_repo", lambda: fake_route_repo)

    payload = CreateTripRequest(
        route_id=route_id,
        vehicle_id=vehicle_id,
        departure_date=future_date,
        departure_time=time(14, 30),
    )

    with pytest.raises(RouteNotFoundError) as exc_info:
        create_trip_service.create_trip(session, driver_id=driver_id, payload=payload)

    assert exc_info.value.route_id == route_id


def test_create_trip_route_forbidden(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    other_driver_id = uuid4()
    route_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=2)

    fake_route = SimpleNamespace(
        id=route_id,
        driver_id=other_driver_id,
        status=RouteStatus.ACTIVE,
    )
    fake_route_repo = SimpleNamespace(get_by_id=lambda s, rid: fake_route)
    monkeypatch.setattr(create_trip_service, "get_route_repo", lambda: fake_route_repo)

    payload = CreateTripRequest(
        route_id=route_id,
        vehicle_id=vehicle_id,
        departure_date=future_date,
        departure_time=time(14, 30),
    )

    with pytest.raises(RouteForbiddenError):
        create_trip_service.create_trip(session, driver_id=driver_id, payload=payload)


def test_create_trip_route_inactive(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    route_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=2)

    fake_route = SimpleNamespace(
        id=route_id,
        driver_id=driver_id,
        status=RouteStatus.INACTIVE,
    )
    fake_route_repo = SimpleNamespace(get_by_id=lambda s, rid: fake_route)
    monkeypatch.setattr(create_trip_service, "get_route_repo", lambda: fake_route_repo)

    payload = CreateTripRequest(
        route_id=route_id,
        vehicle_id=vehicle_id,
        departure_date=future_date,
        departure_time=time(14, 30),
    )

    with pytest.raises(RouteNotActiveError):
        create_trip_service.create_trip(session, driver_id=driver_id, payload=payload)


def test_create_trip_vehicle_not_found(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    route_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=2)

    fake_route = SimpleNamespace(
        id=route_id,
        driver_id=driver_id,
        status=RouteStatus.ACTIVE,
    )
    fake_route_repo = SimpleNamespace(get_by_id=lambda s, rid: fake_route)
    monkeypatch.setattr(create_trip_service, "get_route_repo", lambda: fake_route_repo)

    fake_vehicle_repo = SimpleNamespace(get_by_id=lambda s, vid: None)
    monkeypatch.setattr(create_trip_service, "get_vehicle_repo", lambda: fake_vehicle_repo)

    from app.features.vehicles.exceptions import VehicleNotFoundError

    payload = CreateTripRequest(
        route_id=route_id,
        vehicle_id=vehicle_id,
        departure_date=future_date,
        departure_time=time(14, 30),
    )

    with pytest.raises(VehicleNotFoundError) as exc_info:
        create_trip_service.create_trip(session, driver_id=driver_id, payload=payload)

    assert exc_info.value.vehicle_id == vehicle_id


def test_create_trip_vehicle_forbidden(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    other_driver_id = uuid4()
    route_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=2)

    fake_route = SimpleNamespace(
        id=route_id,
        driver_id=driver_id,
        status=RouteStatus.ACTIVE,
    )
    fake_route_repo = SimpleNamespace(get_by_id=lambda s, rid: fake_route)
    monkeypatch.setattr(create_trip_service, "get_route_repo", lambda: fake_route_repo)

    fake_vehicle = SimpleNamespace(
        id=vehicle_id,
        driver_id=other_driver_id,
        total_seats=5,
    )
    fake_vehicle_repo = SimpleNamespace(get_by_id=lambda s, vid: fake_vehicle)
    monkeypatch.setattr(create_trip_service, "get_vehicle_repo", lambda: fake_vehicle_repo)

    from app.features.vehicles.exceptions import VehicleForbiddenError

    payload = CreateTripRequest(
        route_id=route_id,
        vehicle_id=vehicle_id,
        departure_date=future_date,
        departure_time=time(14, 30),
    )

    with pytest.raises(VehicleForbiddenError):
        create_trip_service.create_trip(session, driver_id=driver_id, payload=payload)


def test_create_trip_invalid_vehicle_seats(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    route_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=2)

    fake_route = SimpleNamespace(
        id=route_id,
        driver_id=driver_id,
        status=RouteStatus.ACTIVE,
    )
    fake_route_repo = SimpleNamespace(get_by_id=lambda s, rid: fake_route)
    monkeypatch.setattr(create_trip_service, "get_route_repo", lambda: fake_route_repo)

    fake_vehicle = SimpleNamespace(
        id=vehicle_id,
        driver_id=driver_id,
        total_seats=1,
    )
    fake_vehicle_repo = SimpleNamespace(get_by_id=lambda s, vid: fake_vehicle)
    monkeypatch.setattr(create_trip_service, "get_vehicle_repo", lambda: fake_vehicle_repo)

    payload = CreateTripRequest(
        route_id=route_id,
        vehicle_id=vehicle_id,
        departure_date=future_date,
        departure_time=time(14, 30),
    )

    with pytest.raises(InvalidAvailableSeatsError):
        create_trip_service.create_trip(session, driver_id=driver_id, payload=payload)


def test_create_trip_past_departure(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    route_id = uuid4()
    vehicle_id = uuid4()
    past_date = date.today() - timedelta(days=1)

    fake_route = SimpleNamespace(
        id=route_id,
        driver_id=driver_id,
        status=RouteStatus.ACTIVE,
    )
    fake_route_repo = SimpleNamespace(get_by_id=lambda s, rid: fake_route)
    monkeypatch.setattr(create_trip_service, "get_route_repo", lambda: fake_route_repo)

    fake_vehicle = SimpleNamespace(
        id=vehicle_id,
        driver_id=driver_id,
        total_seats=5,
    )
    fake_vehicle_repo = SimpleNamespace(get_by_id=lambda s, vid: fake_vehicle)
    monkeypatch.setattr(create_trip_service, "get_vehicle_repo", lambda: fake_vehicle_repo)

    payload = CreateTripRequest(
        route_id=route_id,
        vehicle_id=vehicle_id,
        departure_date=past_date,
        departure_time=time(8, 0),
    )

    with pytest.raises(PastDepartureError):
        create_trip_service.create_trip(session, driver_id=driver_id, payload=payload)



# =============================================================================
# get_trip
# =============================================================================


def test_get_trip_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    trip_id = uuid4()
    fake_trip = make_fake_trip(trip_id=trip_id, driver_id=driver_id)

    fake_repo = SimpleNamespace(get_by_id=lambda s, tid: fake_trip)
    monkeypatch.setattr(get_trip_service, "get_trip_repo", lambda: fake_repo)

    result = get_trip_service.get_trip(session, trip_id=trip_id, driver_id=driver_id)
    assert result == fake_trip


def test_get_trip_not_found(monkeypatch):
    session = FakeSession()
    trip_id = uuid4()

    fake_repo = SimpleNamespace(get_by_id=lambda s, tid: None)
    monkeypatch.setattr(get_trip_service, "get_trip_repo", lambda: fake_repo)

    with pytest.raises(TripNotFoundError):
        get_trip_service.get_trip(session, trip_id=trip_id)


def test_get_trip_forbidden(monkeypatch):
    session = FakeSession()
    trip_id = uuid4()
    owner_id = uuid4()
    other_id = uuid4()
    fake_trip = make_fake_trip(trip_id=trip_id, driver_id=owner_id)

    fake_repo = SimpleNamespace(get_by_id=lambda s, tid: fake_trip)
    monkeypatch.setattr(get_trip_service, "get_trip_repo", lambda: fake_repo)

    with pytest.raises(TripForbiddenError):
        get_trip_service.get_trip(session, trip_id=trip_id, driver_id=other_id)


# =============================================================================
# list_driver_trips
# =============================================================================


def test_list_driver_trips_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    fake_trips = [make_fake_trip(driver_id=driver_id)]

    fake_repo = SimpleNamespace(list_by_driver=lambda s, **kw: (fake_trips, 1))
    monkeypatch.setattr(list_trips_service, "get_trip_repo", lambda: fake_repo)

    items, total = list_trips_service.list_driver_trips(session, driver_id=driver_id)
    assert items == fake_trips
    assert total == 1


def test_list_driver_trips_invalid_pagination():
    session = FakeSession()
    driver_id = uuid4()

    with pytest.raises(InvalidPaginationError):
        list_trips_service.list_driver_trips(session, driver_id=driver_id, limit=-1, offset=0)


# =============================================================================
# update_trip
# =============================================================================


def test_update_trip_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    trip_id = uuid4()
    vehicle_id = uuid4()
    future_date = date.today() + timedelta(days=3)

    existing_trip = make_fake_trip(
        trip_id=trip_id,
        driver_id=driver_id,
        vehicle_id=vehicle_id,
        status=TripStatus.SCHEDULED,
    )
    updated_trip = make_fake_trip(
        trip_id=trip_id,
        driver_id=driver_id,
        vehicle_id=vehicle_id,
        departure_date=future_date,
    )

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, tid: existing_trip,
        update=lambda s, t, **kw: updated_trip,
    )
    monkeypatch.setattr(update_trip_service, "get_trip_repo", lambda: fake_repo)

    payload = UpdateTripRequest(departure_date=future_date)
    result = update_trip_service.update_trip(session, trip_id=trip_id, driver_id=driver_id, payload=payload)

    assert result == updated_trip
    assert session.committed is True
    assert session.rolled_back is False


def test_update_trip_vehicle_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    trip_id = uuid4()
    old_vehicle_id = uuid4()
    new_vehicle_id = uuid4()

    existing_trip = make_fake_trip(
        trip_id=trip_id,
        driver_id=driver_id,
        vehicle_id=old_vehicle_id,
        status=TripStatus.SCHEDULED,
    )
    updated_trip = make_fake_trip(
        trip_id=trip_id,
        driver_id=driver_id,
        vehicle_id=new_vehicle_id,
        available_seats=4,
    )
    captured = {}

    def fake_update(s, t, **kw):
        captured.update(kw)
        return updated_trip

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, tid: existing_trip,
        update=fake_update,
    )
    monkeypatch.setattr(update_trip_service, "get_trip_repo", lambda: fake_repo)

    fake_vehicle = SimpleNamespace(id=new_vehicle_id, driver_id=driver_id, total_seats=5)
    fake_vehicle_repo = SimpleNamespace(get_by_id=lambda s, vid: fake_vehicle)
    monkeypatch.setattr(update_trip_service, "get_vehicle_repo", lambda: fake_vehicle_repo)

    payload = UpdateTripRequest(vehicle_id=new_vehicle_id)
    result = update_trip_service.update_trip(session, trip_id=trip_id, driver_id=driver_id, payload=payload)

    assert result == updated_trip
    assert session.committed is True
    assert captured["available_seats"] == 4
    assert captured["vehicle_id"] == new_vehicle_id



def test_update_trip_cancelled_status_cannot_be_modified(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    trip_id = uuid4()
    future_date = date.today() + timedelta(days=3)

    existing_trip = make_fake_trip(
        trip_id=trip_id,
        driver_id=driver_id,
        status=TripStatus.CANCELLED,
    )

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, tid: existing_trip,
    )
    monkeypatch.setattr(update_trip_service, "get_trip_repo", lambda: fake_repo)

    payload = UpdateTripRequest(departure_date=future_date)
    with pytest.raises(TripCannotBeModifiedError):
        update_trip_service.update_trip(session, trip_id=trip_id, driver_id=driver_id, payload=payload)


def test_update_trip_past_departure_error(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    trip_id = uuid4()
    past_date = date.today() - timedelta(days=2)

    existing_trip = make_fake_trip(
        trip_id=trip_id,
        driver_id=driver_id,
        status=TripStatus.SCHEDULED,
    )

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, tid: existing_trip,
    )
    monkeypatch.setattr(update_trip_service, "get_trip_repo", lambda: fake_repo)

    payload = UpdateTripRequest(departure_date=past_date)
    with pytest.raises(PastDepartureError):
        update_trip_service.update_trip(session, trip_id=trip_id, driver_id=driver_id, payload=payload)


# =============================================================================
# delete_trip
# =============================================================================


def test_delete_trip_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    trip_id = uuid4()

    existing_trip = make_fake_trip(trip_id=trip_id, driver_id=driver_id, status=TripStatus.SCHEDULED)
    deleted = []

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, tid: existing_trip,
        delete=lambda s, t: deleted.append(t),
    )
    monkeypatch.setattr(delete_trip_service, "get_trip_repo", lambda: fake_repo)

    delete_trip_service.delete_trip(session, trip_id=trip_id, driver_id=driver_id)

    assert deleted == [existing_trip]
    assert session.committed is True
    assert session.rolled_back is False


def test_delete_trip_completed_cannot_be_deleted(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    trip_id = uuid4()

    existing_trip = make_fake_trip(trip_id=trip_id, driver_id=driver_id, status=TripStatus.COMPLETED)

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, tid: existing_trip,
    )
    monkeypatch.setattr(delete_trip_service, "get_trip_repo", lambda: fake_repo)

    with pytest.raises(TripCannotBeDeletedError):
        delete_trip_service.delete_trip(session, trip_id=trip_id, driver_id=driver_id)


def test_delete_trip_already_deleted_cannot_be_deleted(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    trip_id = uuid4()

    existing_trip = make_fake_trip(trip_id=trip_id, driver_id=driver_id, status=TripStatus.DELETED)

    fake_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, tid: existing_trip,
    )
    monkeypatch.setattr(delete_trip_service, "get_trip_repo", lambda: fake_repo)

    with pytest.raises(TripCannotBeDeletedError):
        delete_trip_service.delete_trip(session, trip_id=trip_id, driver_id=driver_id)


# =============================================================================
# search_trips
# =============================================================================


def test_search_trips_success(monkeypatch):
    session = FakeSession()
    source_loc_id = uuid4()
    dest_loc_id = uuid4()
    future_date = date.today() + timedelta(days=2)

    fake_trip = make_fake_trip(
        departure_date=future_date,
        available_seats=3,
        status=TripStatus.SCHEDULED,
    )
    captured = {}

    def fake_search(s, **kwargs):
        captured["session"] = s
        captured.update(kwargs)
        return [fake_trip], 1

    fake_repo = SimpleNamespace(search=fake_search)
    monkeypatch.setattr(search_trips_service, "get_trip_repo", lambda: fake_repo)

    items, total = search_trips_service.search_trips(
        session,
        source_location_id=source_loc_id,
        destination_location_id=dest_loc_id,
        departure_date=future_date,
        seats_needed=2,
        status=TripStatus.SCHEDULED,
        limit=10,
        offset=0,
    )

    assert total == 1
    assert items == [fake_trip]
    assert captured["source_location_id"] == source_loc_id
    assert captured["destination_location_id"] == dest_loc_id
    assert captured["departure_date"] == future_date
    assert captured["seats_needed"] == 2
    assert captured["status"] == TripStatus.SCHEDULED
    assert captured["limit"] == 10
    assert captured["offset"] == 0


def test_search_trips_identical_source_destination_error():
    session = FakeSession()
    same_loc_id = uuid4()

    with pytest.raises(IdenticalSourceDestinationError):
        search_trips_service.search_trips(
            session,
            source_location_id=same_loc_id,
            destination_location_id=same_loc_id,
        )


def test_search_trips_invalid_pagination():
    session = FakeSession()
    source_loc_id = uuid4()
    dest_loc_id = uuid4()

    with pytest.raises(InvalidPaginationError):
        search_trips_service.search_trips(
            session,
            source_location_id=source_loc_id,
            destination_location_id=dest_loc_id,
            limit=0,
            offset=0,
        )

    with pytest.raises(InvalidPaginationError):
        search_trips_service.search_trips(
            session,
            source_location_id=source_loc_id,
            destination_location_id=dest_loc_id,
            limit=10,
            offset=-1,
        )


def test_trip_repo_search_ignores_seats_needed():
    from unittest.mock import MagicMock
    from app.features.trips.repositories.trips import TripRepo

    session = MagicMock()
    session.scalar.return_value = 0
    session.scalars.return_value.all.return_value = []
    repo = TripRepo()

    repo.search(
        session,
        source_location_id=uuid4(),
        destination_location_id=uuid4(),
        seats_needed=5,
    )

    assert session.scalars.call_count == 1
    query = session.scalars.call_args[0][0]
    assert "available_seats" not in str(query.whereclause)



