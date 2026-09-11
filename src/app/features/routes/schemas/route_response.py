from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
    driver_id: UUID
    route_stops: list[RouteStopResponse] = []
