from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.features.trips.domain.enums import TripStatus


class TripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    route_id: UUID
    driver_id: UUID
    vehicle_id: UUID
    departure_date: date
    departure_time: time
    available_seats: int
    status: TripStatus
    created_at: datetime
    updated_at: datetime



class PaginatedTripsResponse(BaseModel):
    items: list[TripResponse]
    page: int
    limit: int
    total: int
