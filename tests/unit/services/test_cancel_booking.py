from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

import app.features.bookings.services.cancel_booking as cancel_booking_service
from app.features.bookings.domain.enums import BookingStatus
from app.features.bookings.exceptions import (
    BookingAlreadyCancelledError,
    BookingCannotBeCancelledError,
    BookingForbiddenError,
    BookingNotFoundError,
    TripNotFoundError,
)


class FakeSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class FakeBookingRepo:
    def __init__(self, booking=None):
        self.booking = booking
        self.updated_status = None

    def get_by_id_for_update(self, session, booking_id: UUID):
        return self.booking

    def update(self, session, booking, *, status=None, seats_booked=None):
        if status is not None:
            booking.status = status
            self.updated_status = status
        return booking


class FakeTripRepo:
    def __init__(self, trip=None):
        self.trip = trip
        self.updated_available_seats = None

    def get_by_id_for_update(self, session, trip_id: UUID):
        return self.trip

    def update(self, session, trip, *, available_seats=None, **kwargs):
        if available_seats is not None:
            trip.available_seats = available_seats
            self.updated_available_seats = available_seats
        return trip


def test_cancel_booking_success(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    booking_id = uuid4()
    trip_id = uuid4()

    fake_booking = SimpleNamespace(
        id=booking_id,
        rider_id=rider_id,
        trip_id=trip_id,
        seats_booked=2,
        status=BookingStatus.PENDING,
    )
    fake_trip = SimpleNamespace(
        id=trip_id,
        available_seats=1,
    )
    fake_booking_repo = FakeBookingRepo(booking=fake_booking)
    fake_trip_repo = FakeTripRepo(trip=fake_trip)

    monkeypatch.setattr(
        cancel_booking_service, "get_booking_repo", lambda: fake_booking_repo
    )
    monkeypatch.setattr(
        cancel_booking_service, "get_trip_repo", lambda: fake_trip_repo
    )

    result = cancel_booking_service.cancel_booking(
        session,
        booking_id=booking_id,
        rider_id=rider_id,
    )

    assert result.status == BookingStatus.CANCELLED
    assert fake_booking_repo.updated_status == BookingStatus.CANCELLED
    assert fake_trip.available_seats == 3
    assert fake_trip_repo.updated_available_seats == 3
    assert session.committed is True
    assert session.rolled_back is False


def test_cancel_booking_confirmed_success(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    booking_id = uuid4()
    trip_id = uuid4()

    fake_booking = SimpleNamespace(
        id=booking_id,
        rider_id=rider_id,
        trip_id=trip_id,
        seats_booked=3,
        status=BookingStatus.CONFIRMED,
    )
    fake_trip = SimpleNamespace(
        id=trip_id,
        available_seats=0,
    )
    fake_booking_repo = FakeBookingRepo(booking=fake_booking)
    fake_trip_repo = FakeTripRepo(trip=fake_trip)

    monkeypatch.setattr(
        cancel_booking_service, "get_booking_repo", lambda: fake_booking_repo
    )
    monkeypatch.setattr(
        cancel_booking_service, "get_trip_repo", lambda: fake_trip_repo
    )

    result = cancel_booking_service.cancel_booking(
        session,
        booking_id=booking_id,
        rider_id=rider_id,
    )

    assert result.status == BookingStatus.CANCELLED
    assert fake_trip.available_seats == 3
    assert session.committed is True


def test_cancel_booking_not_found(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    booking_id = uuid4()

    fake_booking_repo = FakeBookingRepo(booking=None)
    fake_trip_repo = FakeTripRepo(trip=None)
    monkeypatch.setattr(
        cancel_booking_service, "get_booking_repo", lambda: fake_booking_repo
    )
    monkeypatch.setattr(
        cancel_booking_service, "get_trip_repo", lambda: fake_trip_repo
    )

    with pytest.raises(BookingNotFoundError) as exc_info:
        cancel_booking_service.cancel_booking(
            session,
            booking_id=booking_id,
            rider_id=rider_id,
        )

    assert exc_info.value.booking_id == booking_id
    assert session.rolled_back is True


def test_cancel_booking_forbidden_not_owner(monkeypatch):
    session = FakeSession()
    booking_id = uuid4()
    owner_rider_id = uuid4()
    other_rider_id = uuid4()

    fake_booking = SimpleNamespace(
        id=booking_id,
        rider_id=owner_rider_id,
        trip_id=uuid4(),
        seats_booked=1,
        status=BookingStatus.PENDING,
    )
    fake_booking_repo = FakeBookingRepo(booking=fake_booking)
    fake_trip_repo = FakeTripRepo(trip=None)
    monkeypatch.setattr(
        cancel_booking_service, "get_booking_repo", lambda: fake_booking_repo
    )
    monkeypatch.setattr(
        cancel_booking_service, "get_trip_repo", lambda: fake_trip_repo
    )

    with pytest.raises(BookingForbiddenError) as exc_info:
        cancel_booking_service.cancel_booking(
            session,
            booking_id=booking_id,
            rider_id=other_rider_id,
        )

    assert exc_info.value.booking_id == booking_id
    assert exc_info.value.user_id == other_rider_id
    assert session.rolled_back is True


def test_cancel_booking_already_cancelled(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    booking_id = uuid4()

    fake_booking = SimpleNamespace(
        id=booking_id,
        rider_id=rider_id,
        trip_id=uuid4(),
        seats_booked=1,
        status=BookingStatus.CANCELLED,
    )
    fake_booking_repo = FakeBookingRepo(booking=fake_booking)
    fake_trip_repo = FakeTripRepo(trip=None)
    monkeypatch.setattr(
        cancel_booking_service, "get_booking_repo", lambda: fake_booking_repo
    )
    monkeypatch.setattr(
        cancel_booking_service, "get_trip_repo", lambda: fake_trip_repo
    )

    with pytest.raises(BookingAlreadyCancelledError):
        cancel_booking_service.cancel_booking(
            session,
            booking_id=booking_id,
            rider_id=rider_id,
        )

    assert session.rolled_back is True


def test_cancel_booking_cannot_be_cancelled_expired(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    booking_id = uuid4()

    fake_booking = SimpleNamespace(
        id=booking_id,
        rider_id=rider_id,
        trip_id=uuid4(),
        seats_booked=1,
        status=BookingStatus.EXPIRED,
    )
    fake_booking_repo = FakeBookingRepo(booking=fake_booking)
    fake_trip_repo = FakeTripRepo(trip=None)
    monkeypatch.setattr(
        cancel_booking_service, "get_booking_repo", lambda: fake_booking_repo
    )
    monkeypatch.setattr(
        cancel_booking_service, "get_trip_repo", lambda: fake_trip_repo
    )

    with pytest.raises(BookingCannotBeCancelledError):
        cancel_booking_service.cancel_booking(
            session,
            booking_id=booking_id,
            rider_id=rider_id,
        )

    assert session.rolled_back is True


def test_cancel_booking_trip_not_found(monkeypatch):
    session = FakeSession()
    rider_id = uuid4()
    booking_id = uuid4()
    trip_id = uuid4()

    fake_booking = SimpleNamespace(
        id=booking_id,
        rider_id=rider_id,
        trip_id=trip_id,
        seats_booked=2,
        status=BookingStatus.PENDING,
    )
    fake_booking_repo = FakeBookingRepo(booking=fake_booking)
    fake_trip_repo = FakeTripRepo(trip=None)

    monkeypatch.setattr(
        cancel_booking_service, "get_booking_repo", lambda: fake_booking_repo
    )
    monkeypatch.setattr(
        cancel_booking_service, "get_trip_repo", lambda: fake_trip_repo
    )

    with pytest.raises(TripNotFoundError) as exc_info:
        cancel_booking_service.cancel_booking(
            session,
            booking_id=booking_id,
            rider_id=rider_id,
        )

    assert exc_info.value.trip_id == trip_id
    assert session.rolled_back is True
