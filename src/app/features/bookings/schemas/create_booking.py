from uuid import UUID

from pydantic import BaseModel, Field


class CreateBookingRequest(BaseModel):
    trip_id: UUID
    pickup_stop_id: UUID
    dropoff_stop_id: UUID
    seats_booked: int = Field(default=1, ge=1)
