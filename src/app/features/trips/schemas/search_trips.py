from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.features.trips.schemas.trip_response import TripResponse


class SearchTripsRequest(BaseModel):
    source_location_id: UUID
    destination_location_id: UUID
    departure_date: date | None = None
    seats_needed: int | None = Field(default=None, ge=1)


class SearchTripsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[TripResponse]
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1)
    total: int = Field(default=0, ge=0)
