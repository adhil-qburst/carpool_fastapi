from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.features.bookings.domain.enums import BookingStatus
from app.features.routes.schemas.route_response import RouteStopResponse


class PassengerUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str


class PassengerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_id: UUID
    rider_id: UUID
    rider_name: str
    rider_email: str
    rider: PassengerUserResponse
    seats_booked: int
    status: BookingStatus
    pickup_stop: RouteStopResponse
    dropoff_stop: RouteStopResponse
    created_at: datetime
    updated_at: datetime
