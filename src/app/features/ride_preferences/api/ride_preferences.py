from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.ride_preferences.exceptions import (
    DuplicateRidePreferenceError,
    InvalidRidePreferenceLabelError,
    InvalidSeatsNeededError,
    RidePreferenceForbiddenError,
    RidePreferenceNotFoundError,
    SameLocationRidePreferenceError,
)
from app.features.ride_preferences.schemas.create_ride_preference import (
    CreateRidePreferenceRequest,
)
from app.features.ride_preferences.schemas.ride_preference_response import (
    RidePreferenceResponse,
)
from app.features.ride_preferences.schemas.update_ride_preference import (
    UpdateRidePreferenceRequest,
)
from app.features.ride_preferences.services.create_ride_preference import (
    create_ride_preference,
)
from app.features.ride_preferences.services.delete_ride_preference import (
    delete_ride_preference,
)
from app.features.ride_preferences.services.get_ride_preference import (
    get_ride_preference,
)
from app.features.ride_preferences.services.list_ride_preferences import (
    list_active_preferences_by_locations,
    list_user_ride_preferences,
)
from app.features.ride_preferences.services.update_ride_preference import (
    update_ride_preference,
)

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RidePreferenceResponse,
)
def create_new_ride_preference(
    payload: CreateRidePreferenceRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> RidePreferenceResponse:
    try:
        return create_ride_preference(
            session=db,
            rider_id=current_user_id,
            source_location_id=payload.source_location_id,
            destination_location_id=payload.destination_location_id,
            preferred_departure_time=payload.preferred_departure_time,
            seats_needed=payload.seats_needed,
            is_active=payload.is_active,
            label=payload.label,
        )
    except SameLocationRidePreferenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except InvalidSeatsNeededError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except InvalidRidePreferenceLabelError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except DuplicateRidePreferenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[RidePreferenceResponse],
)
def list_preferences(
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> list[RidePreferenceResponse]:
    return list_user_ride_preferences(
        session=db,
        rider_id=current_user_id,
        active_only=active_only,
    )


@router.get(
    "/matches",
    status_code=status.HTTP_200_OK,
    response_model=list[RidePreferenceResponse],
)
def list_matching_preferences(
    source_location_id: UUID = Query(...),
    destination_location_id: UUID = Query(...),
    db: Session = Depends(get_db),
    _current_user_id: UUID = Depends(get_current_user_id),
) -> list[RidePreferenceResponse]:
    try:
        return list_active_preferences_by_locations(
            session=db,
            source_location_id=source_location_id,
            destination_location_id=destination_location_id,
        )
    except SameLocationRidePreferenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc


@router.get(
    "/{preference_id}",
    status_code=status.HTTP_200_OK,
    response_model=RidePreferenceResponse,
)
def get_preference(
    preference_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> RidePreferenceResponse:
    try:
        return get_ride_preference(
            session=db,
            ride_preference_id=preference_id,
            rider_id=current_user_id,
        )
    except RidePreferenceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except RidePreferenceForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc


@router.patch(
    "/{preference_id}",
    status_code=status.HTTP_200_OK,
    response_model=RidePreferenceResponse,
)
def update_preference(
    preference_id: UUID,
    payload: UpdateRidePreferenceRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> RidePreferenceResponse:
    try:
        return update_ride_preference(
            session=db,
            ride_preference_id=preference_id,
            rider_id=current_user_id,
            source_location_id=payload.source_location_id,
            destination_location_id=payload.destination_location_id,
            preferred_departure_time=payload.preferred_departure_time,
            seats_needed=payload.seats_needed,
            is_active=payload.is_active,
            label=payload.label,
        )
    except RidePreferenceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except RidePreferenceForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
    except SameLocationRidePreferenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except InvalidSeatsNeededError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except InvalidRidePreferenceLabelError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except DuplicateRidePreferenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc


@router.delete(
    "/{preference_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_ride_preference(
    preference_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> None:
    try:
        delete_ride_preference(
            session=db,
            ride_preference_id=preference_id,
            rider_id=current_user_id,
        )
    except RidePreferenceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except RidePreferenceForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
