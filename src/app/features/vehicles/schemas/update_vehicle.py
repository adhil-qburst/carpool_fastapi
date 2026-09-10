from pydantic import BaseModel, Field, field_validator


class UpdateVehicleRequest(BaseModel):
    make: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, min_length=1, max_length=100)
    registration_number: str | None = Field(default=None, min_length=1, max_length=50)
    total_seats: int | None = Field(default=None, gt=0, le=50)

    @field_validator("make", "model")
    @classmethod
    def string_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty")
        return stripped

    @field_validator("registration_number")
    @classmethod
    def registration_number_must_be_normalized(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip().upper()
        if not stripped:
            raise ValueError("Registration number cannot be empty")
        return stripped
