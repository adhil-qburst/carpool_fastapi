from datetime import time
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CreateRidePreferenceRequest(BaseModel):
    source_location_id: UUID
    destination_location_id: UUID
    preferred_departure_time: time | None = None
    seats_needed: int = Field(default=1, ge=1)
    is_active: bool = True
    label: str | None = Field(default=None, max_length=100)

    @field_validator("label")
    @classmethod
    def normalize_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed if trimmed else None
