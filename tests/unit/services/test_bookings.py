from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

import app.features.bookings.services.create_booking as create_booking_service
from app.features.bookings.domain.enums import BookingStatus
from app.features.bookings.exceptions import (
    DriverCannotBookOwnTripError,
    InsufficientSeatsError,
    InvalidStopSequenceError,
    PastDepartureError,
    RouteStopNotFoundError,
    StopNotInTripRouteError,
    TripNotAvailableForBookingError,
    TripNotFoundError,
)
from app.features.bookings.schemas.create_booking import CreateBookingRequest
from app.features.trips.domain.enums import TripStatus


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
    departure_date: date | None = None,
    departure_time: time | None = None,
    available_seats: int = 4,
    status: TripStatus = TripStatus.SCHEDULED,
) -> SimpleNamespace:
    future_date = date.today() + timedelta(days=2)
    return SimpleNamespace(
        id=trip_id or uuid4(),
        route_id=route_id or uuid4(),
        driver_id=driver_id or uuid4(),
        departure_date=departure_date or future_date,
        departure_time=departure_time or time(10, 0),
        available_seats=available_seats,
        status=status,
    )


def test_create_booking_success(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    driver_id = uuid4()
    route_id = uuid4()
    trip_id = uuid4()
    pickup_stop_id = uuid4()
    dropoff_stop_id = uuid4()

    fake_trip = make_fake_trip(
        trip_id=trip_id,
        route_id=route_id,
        driver_id=driver_id,
        available_seats=4,
    )
    captured_trip_update = {}

    def fake_update(s, trip, **kwargs):
        captured_trip_update.update(kwargs)
        for k, v in kwargs.items():
            if v is not None:
                setattr(trip, k, v)
        return trip

    fake_trip_repo = SimpleNamespace(
        get_by_id_for_update=lambda s, tid: fake_trip,
        update=fake_update,
    )
    monkeypatch.setattr(create_booking_service, "get_trip_repo", lambda: fake_trip_repo)

    fake_pickup_stop = SimpleNamespace(id=pickup_stop_id, route_id=route_id, sequence=1)
    fake_dropoff_stop = SimpleNamespace(id=dropoff_stop_id, route_id=route_id, sequence=3)

    def fake_get_stop(s, stop_id):
        if stop_id == pickup_stop_id:
            return fake_pickup_stop
        if stop_id == dropoff_stop_id:
            return fake_dropoff_stop
        return None

    fake_route_stop_repo = SimpleNamespace(get_by_id=fake_get_stop)
    monkeypatch.setattr(
        create_booking_service, "get_route_stop_repo", lambda: fake_route_stop_repo
    )

    fake_booking = SimpleNamespace(
        id=uuid4(),
        rider_id=rider_id,
        trip_id=trip_id,
        pickup_stop_id=pickup_stop_id,
        dropoff_stop_id=dropoff_stop_id,
        seats_booked=2,
        status=BookingStatus.PENDING,
    )
    captured_booking_create = {}

    def fake_create(s, **kwargs):
        captured_booking_create.update(kwargs)
        return fake_booking

    fake_booking_repo = SimpleNamespace(create=fake_create)
    monkeypatch.setattr(
        create_booking_service, "get_booking_repo", lambda: fake_booking_repo
    )

    payload = CreateBookingRequest(
        trip_id=trip_id,
        pickup_stop_id=pickup_stop_id,
        dropoff_stop_id=dropoff_stop_id,
        seats_booked=2,
    )

    result = create_booking_service.create_booking(session, rider_id=rider_id, payload=payload)

    assert result == fake_booking
    assert session.committed is True
    assert session.rolled_back is False
    assert captured_trip_update["available_seats"] == 2
    assert fake_trip.available_seats == 2
    assert captured_booking_create["rider_id"] == rider_id
    assert captured_booking_create["trip_id"] == trip_id
    assert captured_booking_create["pickup_stop_id"] == pickup_stop_id
    assert captured_booking_create["dropoff_stop_id"] == dropoff_stop_id
    assert captured_booking_create["seats_booked"] == 2
    assert captured_booking_create["status"] == BookingStatus.PENDING


def test_create_booking_trip_not_found(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    trip_id = uuid4()

    fake_trip_repo = SimpleNamespace(get_by_id_for_update=lambda s, tid: None)
    monkeypatch.setattr(create_booking_service, "get_trip_repo", lambda: fake_trip_repo)

    payload = CreateBookingRequest(
        trip_id=trip_id,
        pickup_stop_id=uuid4(),
        dropoff_stop_id=uuid4(),
        seats_booked=1,
    )

    with pytest.raises(TripNotFoundError) as exc_info:
        create_booking_service.create_booking(session, rider_id=rider_id, payload=payload)

    assert exc_info.value.trip_id == trip_id
    assert session.rolled_back is True


def test_create_booking_driver_cannot_book_own_trip(monkeypatch):
    session = FakeSession()
    driver_id = uuid4()
    trip_id = uuid4()

    fake_trip = make_fake_trip(trip_id=trip_id, driver_id=driver_id)
    fake_trip_repo = SimpleNamespace(get_by_id_for_update=lambda s, tid: fake_trip)
    monkeypatch.setattr(create_booking_service, "get_trip_repo", lambda: fake_trip_repo)

    payload = CreateBookingRequest(
        trip_id=trip_id,
        pickup_stop_id=uuid4(),
        dropoff_stop_id=uuid4(),
        seats_booked=1,
    )

    with pytest.raises(DriverCannotBookOwnTripError):
        create_booking_service.create_booking(session, rider_id=driver_id, payload=payload)

    assert session.rolled_back is True


def test_create_booking_trip_not_scheduled(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    trip_id = uuid4()

    fake_trip = make_fake_trip(trip_id=trip_id, status=TripStatus.CANCELLED)
    fake_trip_repo = SimpleNamespace(get_by_id_for_update=lambda s, tid: fake_trip)
    monkeypatch.setattr(create_booking_service, "get_trip_repo", lambda: fake_trip_repo)

    payload = CreateBookingRequest(
        trip_id=trip_id,
        pickup_stop_id=uuid4(),
        dropoff_stop_id=uuid4(),
        seats_booked=1,
    )

    with pytest.raises(TripNotAvailableForBookingError):
        create_booking_service.create_booking(session, rider_id=rider_id, payload=payload)

    assert session.rolled_back is True


def test_create_booking_past_departure(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    trip_id = uuid4()
    past_date = date.today() - timedelta(days=2)

    fake_trip = make_fake_trip(trip_id=trip_id, departure_date=past_date)
    fake_trip_repo = SimpleNamespace(get_by_id_for_update=lambda s, tid: fake_trip)
    monkeypatch.setattr(create_booking_service, "get_trip_repo", lambda: fake_trip_repo)

    payload = CreateBookingRequest(
        trip_id=trip_id,
        pickup_stop_id=uuid4(),
        dropoff_stop_id=uuid4(),
        seats_booked=1,
    )

    with pytest.raises(PastDepartureError):
        create_booking_service.create_booking(session, rider_id=rider_id, payload=payload)

    assert session.rolled_back is True


def test_create_booking_insufficient_seats(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    trip_id = uuid4()

    fake_trip = make_fake_trip(trip_id=trip_id, available_seats=1)
    fake_trip_repo = SimpleNamespace(get_by_id_for_update=lambda s, tid: fake_trip)
    monkeypatch.setattr(create_booking_service, "get_trip_repo", lambda: fake_trip_repo)

    payload = CreateBookingRequest(
        trip_id=trip_id,
        pickup_stop_id=uuid4(),
        dropoff_stop_id=uuid4(),
        seats_booked=2,
    )

    with pytest.raises(InsufficientSeatsError) as exc_info:
        create_booking_service.create_booking(session, rider_id=rider_id, payload=payload)

    assert exc_info.value.requested_seats == 2
    assert exc_info.value.available_seats == 1
    assert session.rolled_back is True


def test_create_booking_pickup_stop_not_found(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    trip_id = uuid4()
    route_id = uuid4()
    pickup_stop_id = uuid4()

    fake_trip = make_fake_trip(trip_id=trip_id, route_id=route_id, available_seats=4)
    fake_trip_repo = SimpleNamespace(get_by_id_for_update=lambda s, tid: fake_trip)
    monkeypatch.setattr(create_booking_service, "get_trip_repo", lambda: fake_trip_repo)

    fake_route_stop_repo = SimpleNamespace(get_by_id=lambda s, sid: None)
    monkeypatch.setattr(
        create_booking_service, "get_route_stop_repo", lambda: fake_route_stop_repo
    )

    payload = CreateBookingRequest(
        trip_id=trip_id,
        pickup_stop_id=pickup_stop_id,
        dropoff_stop_id=uuid4(),
        seats_booked=1,
    )

    with pytest.raises(RouteStopNotFoundError) as exc_info:
        create_booking_service.create_booking(session, rider_id=rider_id, payload=payload)

    assert exc_info.value.stop_id == pickup_stop_id
    assert session.rolled_back is True


def test_create_booking_stop_not_in_route(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    trip_id = uuid4()
    route_id = uuid4()
    other_route_id = uuid4()
    pickup_stop_id = uuid4()

    fake_trip = make_fake_trip(trip_id=trip_id, route_id=route_id, available_seats=4)
    fake_trip_repo = SimpleNamespace(get_by_id_for_update=lambda s, tid: fake_trip)
    monkeypatch.setattr(create_booking_service, "get_trip_repo", lambda: fake_trip_repo)

    fake_pickup_stop = SimpleNamespace(id=pickup_stop_id, route_id=other_route_id, sequence=1)
    fake_route_stop_repo = SimpleNamespace(get_by_id=lambda s, sid: fake_pickup_stop)
    monkeypatch.setattr(
        create_booking_service, "get_route_stop_repo", lambda: fake_route_stop_repo
    )

    payload = CreateBookingRequest(
        trip_id=trip_id,
        pickup_stop_id=pickup_stop_id,
        dropoff_stop_id=uuid4(),
        seats_booked=1,
    )

    with pytest.raises(StopNotInTripRouteError) as exc_info:
        create_booking_service.create_booking(session, rider_id=rider_id, payload=payload)

    assert exc_info.value.stop_id == pickup_stop_id
    assert exc_info.value.route_id == route_id
    assert session.rolled_back is True


def test_create_booking_invalid_stop_sequence(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    trip_id = uuid4()
    route_id = uuid4()
    pickup_stop_id = uuid4()
    dropoff_stop_id = uuid4()

    fake_trip = make_fake_trip(trip_id=trip_id, route_id=route_id, available_seats=4)
    fake_trip_repo = SimpleNamespace(get_by_id_for_update=lambda s, tid: fake_trip)
    monkeypatch.setattr(create_booking_service, "get_trip_repo", lambda: fake_trip_repo)

    fake_pickup_stop = SimpleNamespace(id=pickup_stop_id, route_id=route_id, sequence=3)
    fake_dropoff_stop = SimpleNamespace(id=dropoff_stop_id, route_id=route_id, sequence=1)

    def fake_get_stop(s, stop_id):
        if stop_id == pickup_stop_id:
            return fake_pickup_stop
        if stop_id == dropoff_stop_id:
            return fake_dropoff_stop
        return None

    fake_route_stop_repo = SimpleNamespace(get_by_id=fake_get_stop)
    monkeypatch.setattr(
        create_booking_service, "get_route_stop_repo", lambda: fake_route_stop_repo
    )

    payload = CreateBookingRequest(
        trip_id=trip_id,
        pickup_stop_id=pickup_stop_id,
        dropoff_stop_id=dropoff_stop_id,
        seats_booked=1,
    )

    with pytest.raises(InvalidStopSequenceError):
        create_booking_service.create_booking(session, rider_id=rider_id, payload=payload)

    assert session.rolled_back is True
