from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.bookings.exceptions import (
    DriverCannotBookOwnTripError,
    InsufficientSeatsError,
    InvalidBookingSeatsError,
    InvalidStopSequenceError,
    PastDepartureError,
    RouteStopNotFoundError,
    StopNotInTripRouteError,
    TripNotAvailableForBookingError,
    TripNotFoundError,
)
from app.features.bookings.schemas.booking_response import BookingResponse
from app.features.bookings.schemas.create_booking import CreateBookingRequest
from app.features.bookings.services.create_booking import create_booking

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=BookingResponse,
)
def create_new_booking(
    payload: CreateBookingRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> BookingResponse:
    try:
        return create_booking(
            session=db,
            rider_id=current_user_id,
            payload=payload,
        )
    except TripNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except RouteStopNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except InsufficientSeatsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc
    except TripNotAvailableForBookingError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc
    except DriverCannotBookOwnTripError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except InvalidBookingSeatsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except InvalidStopSequenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except PastDepartureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except StopNotInTripRouteError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
