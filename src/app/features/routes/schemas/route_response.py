from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.features.routes.domain.enums import RouteStatus


class RouteStopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    route_id: UUID
    location_id: UUID
    sequence: int


class RouteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: RouteStatus = RouteStatus.ACTIVE
    driver_id: UUID
    route_stops: list[RouteStopResponse] = []


class PaginatedRoutesResponse(BaseModel):
    items: list[RouteResponse]
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
