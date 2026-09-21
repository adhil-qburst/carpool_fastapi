from datetime import datetime
from uuid import UUID

from app.features.routes.schemas.route_response import RouteStopResponse
from pydantic import BaseModel, ConfigDict, Field

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
    pickup_stop: RouteStopResponse
    dropoff_stop: RouteStopResponse
    created_at: datetime
    updated_at: datetime


class PaginatedBookingsResponse(BaseModel):
    items: list[BookingResponse]
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1)
    total: int = Field(..., ge=0)

