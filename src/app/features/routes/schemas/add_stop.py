from uuid import UUID

from pydantic import BaseModel, Field


class AddStopRequest(BaseModel):
    location_id: UUID
    sequence: int | None = Field(default=None, ge=0)
