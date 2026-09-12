from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.features.location.domain.enums import LocationStatus


class CreateLocationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=255)
    lat: Decimal | None = Field(default=None, ge=-90, le=90)
    lng: Decimal | None = Field(default=None, ge=-180, le=180)
    status: LocationStatus = LocationStatus.ACTIVE

    @field_validator("name", "city")
    @classmethod
    def string_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty")
        return stripped
