from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.features.bookings.domain.enums import BookingStatus


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rider_id: UUID
    trip_id: UUID
    pickup_stop_id: UUID
    dropoff_stop_id: UUID
    seats_booked: int
    status: BookingStatus
    created_at: datetime
    updated_at: datetime
