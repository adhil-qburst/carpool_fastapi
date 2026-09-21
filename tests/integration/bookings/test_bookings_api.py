from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.bookings.api import bookings
from app.features.bookings.domain.enums import BookingStatus
from app.features.bookings.exceptions import (
    BookingAlreadyCancelledError,
    BookingCannotBeCancelledError,
    BookingForbiddenError,
    BookingNotFoundError,
    DriverCannotBookOwnTripError,
    InsufficientSeatsError,
    InvalidBookingSeatsError,
    InvalidPaginationError,
    InvalidStopSequenceError,
    PastDepartureError,
    RouteStopNotFoundError,
    StopNotInTripRouteError,
    TripNotAvailableForBookingError,
    TripNotFoundError,
)
from app.main import app

TEST_USER_ID = UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def auth_client(client):
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    yield client
    app.dependency_overrides.clear()


def make_fake_booking(
    booking_id: UUID | None = None,
    rider_id: UUID | None = None,
    trip_id: UUID | None = None,
    pickup_stop_id: UUID | None = None,
    dropoff_stop_id: UUID | None = None,
    seats_booked: int = 2,
    status: BookingStatus = BookingStatus.PENDING,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    p_id = pickup_stop_id or uuid4()
    d_id = dropoff_stop_id or uuid4()
    return SimpleNamespace(
        id=booking_id or uuid4(),
        rider_id=rider_id or TEST_USER_ID,
        trip_id=trip_id or uuid4(),
        pickup_stop_id=p_id,
        dropoff_stop_id=d_id,
        seats_booked=seats_booked,
        status=status,
        pickup_stop=SimpleNamespace(
            id=p_id,
            route_id=uuid4(),
            location_id=uuid4(),
            sequence=1,
            location=None,
        ),
        dropoff_stop=SimpleNamespace(
            id=d_id,
            route_id=uuid4(),
            location_id=uuid4(),
            sequence=2,
            location=None,
        ),
        created_at=now,
        updated_at=now,
    )



# =============================================================================
# POST /api/v1/bookings
# =============================================================================


def test_create_booking_success(auth_client, monkeypatch):
    trip_id = uuid4()
    pickup_id = uuid4()
    dropoff_id = uuid4()
    booking_id = uuid4()

    fake_booking = make_fake_booking(
        booking_id=booking_id,
        rider_id=TEST_USER_ID,
        trip_id=trip_id,
        pickup_stop_id=pickup_id,
        dropoff_stop_id=dropoff_id,
        seats_booked=2,
    )

    monkeypatch.setattr(
        bookings,
        "create_booking",
        lambda session, rider_id, payload: fake_booking,
    )

    response = auth_client.post(
        "/api/v1/bookings",
        json={
            "trip_id": str(trip_id),
            "pickup_stop_id": str(pickup_id),
            "dropoff_stop_id": str(dropoff_id),
            "seats_booked": 2,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(booking_id)
    assert data["rider_id"] == str(TEST_USER_ID)
    assert data["trip_id"] == str(trip_id)
    assert data["pickup_stop_id"] == str(pickup_id)
    assert data["dropoff_stop_id"] == str(dropoff_id)
    assert data["seats_booked"] == 2
    assert data["status"] == BookingStatus.PENDING.value
    assert "created_at" in data
    assert "updated_at" in data


def test_create_booking_unauthenticated(client):
    response = client.post(
        "/api/v1/bookings",
        json={
            "trip_id": str(uuid4()),
            "pickup_stop_id": str(uuid4()),
            "dropoff_stop_id": str(uuid4()),
            "seats_booked": 1,
        },
    )
    assert response.status_code == 401


def test_create_booking_trip_not_found(auth_client, monkeypatch):
    def fake_create(*args, **kwargs):
        raise TripNotFoundError(trip_id=uuid4())

    monkeypatch.setattr(bookings, "create_booking", fake_create)

    response = auth_client.post(
        "/api/v1/bookings",
        json={
            "trip_id": str(uuid4()),
            "pickup_stop_id": str(uuid4()),
            "dropoff_stop_id": str(uuid4()),
            "seats_booked": 1,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Trip not found."


def test_create_booking_route_stop_not_found(auth_client, monkeypatch):
    def fake_create(*args, **kwargs):
        raise RouteStopNotFoundError(stop_id=uuid4())

    monkeypatch.setattr(bookings, "create_booking", fake_create)

    response = auth_client.post(
        "/api/v1/bookings",
        json={
            "trip_id": str(uuid4()),
            "pickup_stop_id": str(uuid4()),
            "dropoff_stop_id": str(uuid4()),
            "seats_booked": 1,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Route stop not found."


def test_create_booking_insufficient_seats(auth_client, monkeypatch):
    def fake_create(*args, **kwargs):
        raise InsufficientSeatsError(requested_seats=3, available_seats=1)

    monkeypatch.setattr(bookings, "create_booking", fake_create)

    response = auth_client.post(
        "/api/v1/bookings",
        json={
            "trip_id": str(uuid4()),
            "pickup_stop_id": str(uuid4()),
            "dropoff_stop_id": str(uuid4()),
            "seats_booked": 3,
        },
    )
    assert response.status_code == 409
    assert "Requested 3 seat(s), but only 1 seat(s) are available." in response.json()["detail"]


def test_create_booking_trip_not_available(auth_client, monkeypatch):
    def fake_create(*args, **kwargs):
        raise TripNotAvailableForBookingError(status="cancelled")

    monkeypatch.setattr(bookings, "create_booking", fake_create)

    response = auth_client.post(
        "/api/v1/bookings",
        json={
            "trip_id": str(uuid4()),
            "pickup_stop_id": str(uuid4()),
            "dropoff_stop_id": str(uuid4()),
            "seats_booked": 1,
        },
    )
    assert response.status_code == 409
    assert "Trip with status 'cancelled' is not available for booking." in response.json()["detail"]


def test_create_booking_driver_cannot_book_own_trip(auth_client, monkeypatch):
    def fake_create(*args, **kwargs):
        raise DriverCannotBookOwnTripError()

    monkeypatch.setattr(bookings, "create_booking", fake_create)

    response = auth_client.post(
        "/api/v1/bookings",
        json={
            "trip_id": str(uuid4()),
            "pickup_stop_id": str(uuid4()),
            "dropoff_stop_id": str(uuid4()),
            "seats_booked": 1,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Drivers cannot book seats on their own trip."


def test_create_booking_invalid_booking_seats(auth_client, monkeypatch):
    def fake_create(*args, **kwargs):
        raise InvalidBookingSeatsError()

    monkeypatch.setattr(bookings, "create_booking", fake_create)

    response = auth_client.post(
        "/api/v1/bookings",
        json={
            "trip_id": str(uuid4()),
            "pickup_stop_id": str(uuid4()),
            "dropoff_stop_id": str(uuid4()),
            "seats_booked": 1,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Seats booked must be at least 1."


def test_create_booking_invalid_stop_sequence(auth_client, monkeypatch):
    def fake_create(*args, **kwargs):
        raise InvalidStopSequenceError()

    monkeypatch.setattr(bookings, "create_booking", fake_create)

    response = auth_client.post(
        "/api/v1/bookings",
        json={
            "trip_id": str(uuid4()),
            "pickup_stop_id": str(uuid4()),
            "dropoff_stop_id": str(uuid4()),
            "seats_booked": 1,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Pickup stop must come before dropoff stop on the route."


def test_create_booking_past_departure(auth_client, monkeypatch):
    def fake_create(*args, **kwargs):
        raise PastDepartureError()

    monkeypatch.setattr(bookings, "create_booking", fake_create)

    response = auth_client.post(
        "/api/v1/bookings",
        json={
            "trip_id": str(uuid4()),
            "pickup_stop_id": str(uuid4()),
            "dropoff_stop_id": str(uuid4()),
            "seats_booked": 1,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot book a trip that has already departed."


def test_create_booking_stop_not_in_trip_route(auth_client, monkeypatch):
    def fake_create(*args, **kwargs):
        raise StopNotInTripRouteError()

    monkeypatch.setattr(bookings, "create_booking", fake_create)

    response = auth_client.post(
        "/api/v1/bookings",
        json={
            "trip_id": str(uuid4()),
            "pickup_stop_id": str(uuid4()),
            "dropoff_stop_id": str(uuid4()),
            "seats_booked": 1,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Selected stop does not belong to the trip's route."


def test_create_booking_validation_error(auth_client):
    response = auth_client.post(
        "/api/v1/bookings",
        json={
            "trip_id": "not-a-valid-uuid",
            "pickup_stop_id": str(uuid4()),
            "dropoff_stop_id": str(uuid4()),
            "seats_booked": 0,
        },
    )
    assert response.status_code == 422


# =============================================================================
# DELETE /api/v1/bookings/{booking_id}
# =============================================================================


def test_cancel_booking_success(auth_client, monkeypatch):
    booking_id = uuid4()
    cancelled_called = {}

    def fake_cancel_booking(session, *, booking_id, rider_id, settings=None):
        cancelled_called["booking_id"] = booking_id
        cancelled_called["rider_id"] = rider_id

    monkeypatch.setattr(bookings, "cancel_booking", fake_cancel_booking)

    response = auth_client.delete(f"/api/v1/bookings/{booking_id}")
    assert response.status_code == 204
    assert response.content == b""
    assert cancelled_called["booking_id"] == booking_id
    assert cancelled_called["rider_id"] == TEST_USER_ID


def test_cancel_booking_unauthenticated(client):
    response = client.delete(f"/api/v1/bookings/{uuid4()}")
    assert response.status_code == 401


def test_cancel_booking_not_found(auth_client, monkeypatch):
    booking_id = uuid4()

    def fake_cancel(*args, **kwargs):
        raise BookingNotFoundError(booking_id=booking_id)

    monkeypatch.setattr(bookings, "cancel_booking", fake_cancel)

    response = auth_client.delete(f"/api/v1/bookings/{booking_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found."


def test_cancel_booking_forbidden(auth_client, monkeypatch):
    booking_id = uuid4()

    def fake_cancel(*args, **kwargs):
        raise BookingForbiddenError(booking_id=booking_id)

    monkeypatch.setattr(bookings, "cancel_booking", fake_cancel)

    response = auth_client.delete(f"/api/v1/bookings/{booking_id}")
    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to access or modify this booking."


def test_cancel_booking_already_cancelled(auth_client, monkeypatch):
    booking_id = uuid4()

    def fake_cancel(*args, **kwargs):
        raise BookingAlreadyCancelledError(booking_id=booking_id)

    monkeypatch.setattr(bookings, "cancel_booking", fake_cancel)

    response = auth_client.delete(f"/api/v1/bookings/{booking_id}")
    assert response.status_code == 409
    assert response.json()["detail"] == "Booking is already cancelled."


def test_cancel_booking_cannot_be_cancelled(auth_client, monkeypatch):
    booking_id = uuid4()

    def fake_cancel(*args, **kwargs):
        raise BookingCannotBeCancelledError(booking_id=booking_id, status="expired")

    monkeypatch.setattr(bookings, "cancel_booking", fake_cancel)

    response = auth_client.delete(f"/api/v1/bookings/{booking_id}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Booking with status 'expired' cannot be cancelled."


def test_cancel_booking_invalid_uuid(auth_client):
    response = auth_client.delete("/api/v1/bookings/not-a-valid-uuid")
    assert response.status_code == 422

