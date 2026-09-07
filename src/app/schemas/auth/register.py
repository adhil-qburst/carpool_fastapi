from pydantic import BaseModel, EmailStr, Field, field_validator

from app.domain.users.enums import UserRole


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    roles: list[UserRole] = Field(..., min_length=1)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be empty")
        return stripped

    @field_validator("email")
    @classmethod
    def email_must_be_normalized(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class RegisterResponse(BaseModel):
    message: str
