from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.vehicles.exceptions import (
    VehicleForbiddenError,
    VehicleNotFoundError,
    VehicleRegistrationAlreadyExistsError,
)
from app.features.vehicles.schemas.create_vehicle import CreateVehicleRequest
from app.features.vehicles.schemas.update_vehicle import UpdateVehicleRequest
from app.features.vehicles.schemas.vehicle_response import VehicleResponse
from app.features.vehicles.services.create_vehicle import create_vehicle
from app.features.vehicles.services.delete_vehicle import delete_vehicle
from app.features.vehicles.services.get_vehicle import get_vehicle
from app.features.vehicles.services.list_vehicles import list_user_vehicles
from app.features.vehicles.services.update_vehicle import update_vehicle

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=VehicleResponse,
)
def register_vehicle(
    payload: CreateVehicleRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> VehicleResponse:
    try:
        return create_vehicle(db, driver_id=current_user_id, payload=payload)
    except VehicleRegistrationAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[VehicleResponse],
)
def list_vehicles(
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> list[VehicleResponse]:
    return list_user_vehicles(db, driver_id=current_user_id)


@router.get(
    "/{vehicle_id}",
    status_code=status.HTTP_200_OK,
    response_model=VehicleResponse,
)
def get_vehicle_by_id(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> VehicleResponse:
    try:
        return get_vehicle(db, vehicle_id=vehicle_id, driver_id=current_user_id)
    except VehicleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except VehicleForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc


@router.patch(
    "/{vehicle_id}",
    status_code=status.HTTP_200_OK,
    response_model=VehicleResponse,
)
def update_vehicle_by_id(
    vehicle_id: UUID,
    payload: UpdateVehicleRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> VehicleResponse:
    try:
        return update_vehicle(
            db,
            vehicle_id=vehicle_id,
            driver_id=current_user_id,
            payload=payload,
        )
    except VehicleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except VehicleForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
    except VehicleRegistrationAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_vehicle_by_id(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> None:
    try:
        delete_vehicle(db, vehicle_id=vehicle_id, driver_id=current_user_id)
    except VehicleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except VehicleForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
