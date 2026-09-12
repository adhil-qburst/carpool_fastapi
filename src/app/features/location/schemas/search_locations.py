from pydantic import BaseModel, Field

from app.features.location.schemas.location_response import LocationResponse


class PaginatedLocationsResponse(BaseModel):
    items: list[LocationResponse]
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
