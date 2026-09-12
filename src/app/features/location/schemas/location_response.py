from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.features.location.domain.enums import LocationStatus


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    city: str
    lat: Decimal | None = None
    lng: Decimal | None = None
    status: LocationStatus
    created_at: datetime
    updated_at: datetime
