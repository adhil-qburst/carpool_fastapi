from datetime import date, time
from uuid import UUID

from pydantic import BaseModel

from app.features.trips.domain.enums import TripStatus


class UpdateTripRequest(BaseModel):
    vehicle_id: UUID | None = None
    departure_date: date | None = None
    departure_time: time | None = None
    status: TripStatus | None = None

