from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.features.routes.schemas.create_route import CreateRouteStopRequest


class UpdateRouteRequest(BaseModel):
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
