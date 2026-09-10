from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.features.users.domain.enums import UserRole


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    email: str
    roles: list[UserRole]
    