from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

import app.features.trips.services.list_passengers as list_passengers_service
from app.features.bookings.domain.enums import BookingStatus
from app.features.trips.domain.enums import TripStatus
from app.features.trips.exceptions import TripForbiddenError, TripNotFoundError


class FakeSession:
    pass


class FakeTripRepo:
    def __init__(self, trip=None):
        self.trip = trip

    def get_by_id(self, session, trip_id: UUID):
        return self.trip


class FakeBookingRepo:
    def __init__(self, bookings=None):
        self.bookings = bookings or []
        self.last_filter_status = None

    def list_by_trip(self, session, *, trip_id: UUID, status: BookingStatus | None = None):
        self.last_filter_status = status
        if status is not None:
            return [b for b in self.bookings if b.status == status]
        return self.bookings


def make_fake_stop(stop_id: UUID | None = None, location_name: str = "Central Station"):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=stop_id or uuid4(),
        route_id=uuid4(),
        location_id=uuid4(),
        sequence=1,
        location=SimpleNamespace(
            id=uuid4(),
            name=location_name,
            city="Metropolis",
            lat=12.9716,
            lng=77.5946,
            status="active",
            created_at=now,
            updated_at=now,
        ),
    )


def make_fake_booking(
    booking_id: UUID | None = None,
    rider_id: UUID | None = None,
    rider_name: str = "Alice Walker",
    rider_email: str = "alice@example.com",
    trip_id: UUID | None = None,
    status: BookingStatus = BookingStatus.CONFIRMED,
    seats_booked: int = 2,
):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=booking_id or uuid4(),
        rider_id=rider_id or uuid4(),
        trip_id=trip_id or uuid4(),
        seats_booked=seats_booked,
        status=status,
        rider=SimpleNamespace(
            id=rider_id or uuid4(),
            name=rider_name,
            email=rider_email,
        ),
        pickup_stop=make_fake_stop(location_name="Origin Stop"),
        dropoff_stop=make_fake_stop(location_name="Destination Stop"),
        created_at=now,
        updated_at=now,
    )


def test_list_trip_passengers_success(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    trip_id = uuid4()

    fake_trip = SimpleNamespace(
        id=trip_id,
        driver_id=driver_id,
        status=TripStatus.SCHEDULED,
    )

    booking_1 = make_fake_booking(
        rider_name="Alice Walker",
        rider_email="alice@example.com",
        trip_id=trip_id,
        status=BookingStatus.CONFIRMED,
        seats_booked=2,
    )
    booking_2 = make_fake_booking(
        rider_name="Bob Stone",
        rider_email="bob@example.com",
        trip_id=trip_id,
        status=BookingStatus.PENDING,
        seats_booked=1,
    )

    fake_trip_repo = FakeTripRepo(fake_trip)
    fake_booking_repo = FakeBookingRepo([booking_1, booking_2])

    monkeypatch.setattr(list_passengers_service, "get_trip_repo", lambda: fake_trip_repo)
    monkeypatch.setattr(list_passengers_service, "get_booking_repo", lambda: fake_booking_repo)

    passengers = list_passengers_service.list_trip_passengers(
        session,
        trip_id=trip_id,
        driver_id=driver_id,
    )

    assert len(passengers) == 2
    assert passengers[0].booking_id == booking_1.id
    assert passengers[0].rider_name == "Alice Walker"
    assert passengers[0].rider_email == "alice@example.com"
    assert passengers[0].status == BookingStatus.CONFIRMED
    assert passengers[0].seats_booked == 2
    assert passengers[0].pickup_stop.location.name == "Origin Stop"

    assert passengers[1].booking_id == booking_2.id
    assert passengers[1].rider_name == "Bob Stone"
    assert passengers[1].status == BookingStatus.PENDING


def test_list_trip_passengers_with_status_filter(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    trip_id = uuid4()

    fake_trip = SimpleNamespace(id=trip_id, driver_id=driver_id)
    booking_1 = make_fake_booking(trip_id=trip_id, status=BookingStatus.CONFIRMED)
    booking_2 = make_fake_booking(trip_id=trip_id, status=BookingStatus.PENDING)

    fake_trip_repo = FakeTripRepo(fake_trip)
    fake_booking_repo = FakeBookingRepo([booking_1, booking_2])

    monkeypatch.setattr(list_passengers_service, "get_trip_repo", lambda: fake_trip_repo)
    monkeypatch.setattr(list_passengers_service, "get_booking_repo", lambda: fake_booking_repo)

    passengers = list_passengers_service.list_trip_passengers(
        session,
        trip_id=trip_id,
        driver_id=driver_id,
        status=BookingStatus.CONFIRMED,
    )

    assert fake_booking_repo.last_filter_status == BookingStatus.CONFIRMED
    assert len(passengers) == 1
    assert passengers[0].status == BookingStatus.CONFIRMED


def test_list_trip_passengers_trip_not_found(monkeypatch):
    session = FakeSession()
    fake_trip_repo = FakeTripRepo(None)

    monkeypatch.setattr(list_passengers_service, "get_trip_repo", lambda: fake_trip_repo)

    with pytest.raises(TripNotFoundError):
        list_passengers_service.list_trip_passengers(
            session,
            trip_id=uuid4(),
            driver_id=uuid4(),
        )


def test_list_trip_passengers_forbidden(monkeypatch):
    session = FakeSession()
    trip_driver_id = uuid4()
    calling_user_id = uuid4()
    trip_id = uuid4()

    fake_trip = SimpleNamespace(id=trip_id, driver_id=trip_driver_id)
    fake_trip_repo = FakeTripRepo(fake_trip)

    monkeypatch.setattr(list_passengers_service, "get_trip_repo", lambda: fake_trip_repo)

    with pytest.raises(TripForbiddenError):
        list_passengers_service.list_trip_passengers(
            session,
            trip_id=trip_id,
            driver_id=calling_user_id,
        )


def test_list_trip_passengers_empty(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    trip_id = uuid4()

    fake_trip = SimpleNamespace(id=trip_id, driver_id=driver_id)
    fake_trip_repo = FakeTripRepo(fake_trip)
    fake_booking_repo = FakeBookingRepo([])

    monkeypatch.setattr(list_passengers_service, "get_trip_repo", lambda: fake_trip_repo)
    monkeypatch.setattr(list_passengers_service, "get_booking_repo", lambda: fake_booking_repo)

    passengers = list_passengers_service.list_trip_passengers(
        session,
        trip_id=trip_id,
        driver_id=driver_id,
    )

    assert passengers == []
