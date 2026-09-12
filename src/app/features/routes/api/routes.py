from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.routes.exceptions import (
    CannotSwapSameStopError,
    DuplicateStopLocationError,
    DuplicateStopSequenceError,
    IdenticalSourceDestinationError,
    InvalidPaginationError,
    InvalidStopSequenceError,
    RouteForbiddenError,
    RouteNameAlreadyExistsError,
    RouteNotFoundError,
    RouteStopNotFoundError,
    StopsDoNotBelongToSameRouteError,
)
from app.features.routes.schemas.add_stop import AddStopRequest
from app.features.routes.schemas.create_route import CreateRouteRequest
from app.features.routes.schemas.route_response import (
    PaginatedRoutesResponse,
    RouteResponse,
    RouteStopResponse,
)
from app.features.routes.schemas.swap_stop import SwapStopsRequest
from app.features.routes.schemas.update_route import UpdateRouteRequest
from app.features.routes.services.add_stop import add_stop
from app.features.routes.services.create_route import create_route
from app.features.routes.services.list_routes import list_user_routes
from app.features.routes.services.swap_stop import swap_stop
from app.features.routes.services.update_route import update_route

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RouteResponse,
)
def create_new_route(
    payload: CreateRouteRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> RouteResponse:
    try:
        try:
            return create_route(
                session=db,
                driver_id=current_user_id,
                name=payload.name,
                source_id=payload.source_id,
                dest_id=payload.dest_id,
                stops=payload.stops,
            )
        except TypeError as exc:
            if "stops" in str(exc):
                return create_route(
                    session=db,
                    driver_id=current_user_id,
                    name=payload.name,
                    source_id=payload.source_id,
                    dest_id=payload.dest_id,
                )
            raise
    except IdenticalSourceDestinationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except RouteNameAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc
    except DuplicateStopLocationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc
    except DuplicateStopSequenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except InvalidStopSequenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedRoutesResponse,
)
def list_routes(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> PaginatedRoutesResponse:
    offset = (page - 1) * limit
    try:
        items, total = list_user_routes(
            session=db,
            driver_id=current_user_id,
            limit=limit,
            offset=offset,
        )
        return PaginatedRoutesResponse(
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


@router.put(
    "/{route_id}",
    status_code=status.HTTP_200_OK,
    response_model=RouteResponse,
)
@router.patch(
    "/{route_id}",
    status_code=status.HTTP_200_OK,
    response_model=RouteResponse,
)
def update_route_by_id(
    route_id: UUID,
    payload: UpdateRouteRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> RouteResponse:
    try:
        return update_route(
            session=db,
            route_id=route_id,
            driver_id=current_user_id,
            name=payload.name,
            source_id=payload.source_id,
            dest_id=payload.dest_id,
            stops=payload.stops,
        )
    except RouteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except RouteForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
    except IdenticalSourceDestinationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except RouteNameAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc
    except DuplicateStopLocationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc
    except DuplicateStopSequenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
    except InvalidStopSequenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc


@router.post(
    "/{route_id}/stops",
    status_code=status.HTTP_201_CREATED,
    response_model=RouteStopResponse,
)
def add_stop_to_route(
    route_id: UUID,
    payload: AddStopRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> RouteStopResponse:
    try:
        return add_stop(
            session=db,
            route_id=route_id,
            location_id=payload.location_id,
            sequence=payload.sequence,
            driver_id=current_user_id,
        )
    except RouteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except RouteForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
    except DuplicateStopLocationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc
    except InvalidStopSequenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc


@router.post(
    "/{route_id}/stops/swap",
    status_code=status.HTTP_200_OK,
    response_model=list[RouteStopResponse],
)
def swap_stops_on_route(
    route_id: UUID,
    payload: SwapStopsRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> list[RouteStopResponse]:
    try:
        stop_1, stop_2 = swap_stop(
            session=db,
            stop_id_1=payload.stop_id_1,
            stop_id_2=payload.stop_id_2,
            route_id=route_id,
            driver_id=current_user_id,
        )
        return [stop_1, stop_2]
    except (RouteNotFoundError, RouteStopNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except RouteForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
    except (CannotSwapSameStopError, StopsDoNotBelongToSameRouteError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc
