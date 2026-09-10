from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    driver_id: UUID
    make: str
    model: str
    registration_number: str
    total_seats: int
    created_at: datetime
    updated_at: datetime
