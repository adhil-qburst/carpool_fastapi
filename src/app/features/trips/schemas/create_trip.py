from datetime import date, time
from uuid import UUID

from pydantic import BaseModel


class CreateTripRequest(BaseModel):
    route_id: UUID
    vehicle_id: UUID
    departure_date: date
    departure_time: time

