from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
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
from app.features.bookings.schemas.booking_response import (
    BookingResponse,
    PaginatedBookingsResponse,
)
from app.features.bookings.schemas.create_booking import CreateBookingRequest
from app.features.bookings.services.cancel_booking import cancel_booking
from app.features.bookings.services.create_booking import create_booking
from app.features.bookings.services.list_bookings import list_user_bookings

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


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedBookingsResponse,
)
def list_bookings(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    booking_status: BookingStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> PaginatedBookingsResponse:
    offset = (page - 1) * limit
    try:
        items, total = list_user_bookings(
            session=db,
            rider_id=current_user_id,
            status=booking_status,
            limit=limit,
            offset=offset,
        )
        return PaginatedBookingsResponse(
            items=items,
            page=page,
            limit=limit,
            total=total,
        )
    except InvalidPaginationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc


@router.delete(
    "/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def cancel_booking_endpoint(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> None:
    try:
        cancel_booking(
            session=db,
            booking_id=booking_id,
            rider_id=current_user_id,
        )
    except BookingNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except TripNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except BookingForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
    except BookingAlreadyCancelledError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc
    except BookingCannotBeCancelledError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc


