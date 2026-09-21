from datetime import time
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UpdateRidePreferenceRequest(BaseModel):
    source_location_id: UUID | None = None
    destination_location_id: UUID | None = None
    preferred_departure_time: time | None = None
    seats_needed: int | None = Field(default=None, ge=1)
    is_active: bool | None = None
    label: str | None = Field(default=None, max_length=100)

    @field_validator("label")
    @classmethod
    def normalize_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed if trimmed else None
