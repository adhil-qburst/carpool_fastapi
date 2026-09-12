from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class CreateRouteStopRequest(BaseModel):
    stop_id: UUID | None = None
    location_id: UUID | None = None
    sequence: int = Field()

    @model_validator(mode="after")
    def validate_ids(self) -> "CreateRouteStopRequest":
        if self.stop_id is None and self.location_id is None:
            raise ValueError("stop_id or location_id must be provided")
        if self.stop_id is None:
            self.stop_id = self.location_id
        return self


class CreateRouteRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    source_id: UUID
    dest_id: UUID
    stops: list[CreateRouteStopRequest] | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Route name cannot be empty")
        return stripped
