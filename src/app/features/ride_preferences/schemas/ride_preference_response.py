from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.features.location.schemas.location_response import LocationResponse
from app.features.users.schemas.current_user import CurrentUserResponse


class RidePreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rider_id: UUID
    source_location_id: UUID
    destination_location_id: UUID
    preferred_departure_time: time | None = None
    seats_needed: int
    is_active: bool
    label: str | None = None
    created_at: datetime
    updated_at: datetime
    source: LocationResponse | None = None
    destination: LocationResponse | None = None
    rider: CurrentUserResponse | None = None
