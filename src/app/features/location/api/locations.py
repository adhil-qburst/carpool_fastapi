from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.location.domain.enums import LocationStatus
from app.features.location.exceptions import (
    InvalidCoordinatesError,
    InvalidPaginationError,
)
from app.features.location.schemas.create_location import CreateLocationRequest
from app.features.location.schemas.location_response import LocationResponse
from app.features.location.schemas.search_locations import PaginatedLocationsResponse
from app.features.location.services.create_location import create_location
from app.features.location.services.search_locations import search_locations

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=LocationResponse,
)
def create_new_location(
    payload: CreateLocationRequest,
    db: Session = Depends(get_db),
) -> LocationResponse:
    try:
        return create_location(
            session=db,
            name=payload.name,
            city=payload.city,
            lat=payload.lat,
            lng=payload.lng,
            status=payload.status,
        )
    except InvalidCoordinatesError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedLocationsResponse,
)
def search_locations_endpoint(
    search: str = Query(default="", max_length=100),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: LocationStatus | None = Query(
        default=LocationStatus.ACTIVE, alias="status"
    ),
    db: Session = Depends(get_db),
) -> PaginatedLocationsResponse:
    offset = (page - 1) * limit
    try:
        items, total = search_locations(
            session=db,
            text=search,
            limit=limit,
            offset=offset,
            status=status_filter,
        )
        return PaginatedLocationsResponse(
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
