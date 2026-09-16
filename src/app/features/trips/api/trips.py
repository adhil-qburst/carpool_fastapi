from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
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
    VehicleSeatsExceededError,
)
from app.features.trips.schemas.create_trip import CreateTripRequest
from app.features.trips.schemas.search_trips import (
    SearchTripsRequest,
    SearchTripsResponse,
)
from app.features.trips.schemas.trip_response import (
    PaginatedTripsResponse,
    TripResponse,
)
from app.features.trips.schemas.update_trip import UpdateTripRequest
from app.features.trips.services.create_trip import create_trip
from app.features.trips.services.delete_trip import delete_trip
from app.features.trips.services.get_trip import get_trip
from app.features.trips.services.list_trips import list_driver_trips
from app.features.trips.services.search_trips import search_trips
from app.features.trips.services.update_trip import update_trip
from app.features.vehicles.exceptions import (
    VehicleForbiddenError,
    VehicleNotFoundError,
)

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TripResponse,
)
def create_new_trip(
    payload: CreateTripRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> TripResponse:
    try:
        return create_trip(
            session=db,
            driver_id=current_user_id,
            payload=payload,
        )
    except RouteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except VehicleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except RouteForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
    except VehicleForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
    except RouteNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except PastDepartureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except InvalidAvailableSeatsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except VehicleSeatsExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedTripsResponse,
)
def list_trips(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> PaginatedTripsResponse:
    offset = (page - 1) * limit
    try:
        items, total = list_driver_trips(
            session=db,
            driver_id=current_user_id,
            limit=limit,
            offset=offset,
        )
        return PaginatedTripsResponse(
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


@router.get(
    "/search",
    status_code=status.HTTP_200_OK,
    response_model=SearchTripsResponse,
)
def search_trips_endpoint(
    source_location_id: UUID = Query(...),
    destination_location_id: UUID = Query(...),
    departure_date: date | None = Query(default=None),
    seats_needed: int | None = Query(default=None, ge=1),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> SearchTripsResponse:
    offset = (page - 1) * limit
    try:
        items, total = search_trips(
            session=db,
            source_location_id=source_location_id,
            destination_location_id=destination_location_id,
            departure_date=departure_date,
            seats_needed=seats_needed,
            status=TripStatus.SCHEDULED,
            limit=limit,
            offset=offset,
        )
        return SearchTripsResponse(
            items=items,
            page=page,
            limit=limit,
            total=total,
        )
    except IdenticalSourceDestinationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except InvalidPaginationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc


@router.get(
    "/{trip_id}",
    status_code=status.HTTP_200_OK,
    response_model=TripResponse,
)
def get_trip_by_id(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> TripResponse:
    try:
        return get_trip(
            session=db,
            trip_id=trip_id,
            driver_id=current_user_id,
        )
    except TripNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except TripForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc


@router.patch(
    "/{trip_id}",
    status_code=status.HTTP_200_OK,
    response_model=TripResponse,
)
@router.put(
    "/{trip_id}",
    status_code=status.HTTP_200_OK,
    response_model=TripResponse,
)
def update_trip_by_id(
    trip_id: UUID,
    payload: UpdateTripRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> TripResponse:
    try:
        return update_trip(
            session=db,
            trip_id=trip_id,
            driver_id=current_user_id,
            payload=payload,
        )
    except TripNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except VehicleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except TripForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
    except VehicleForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
    except TripCannotBeModifiedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except PastDepartureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except InvalidAvailableSeatsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except VehicleSeatsExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc



@router.delete(
    "/{trip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_trip_by_id(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> None:
    try:
        delete_trip(
            session=db,
            trip_id=trip_id,
            driver_id=current_user_id,
        )
    except TripNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except TripForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
    except TripCannotBeDeletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
