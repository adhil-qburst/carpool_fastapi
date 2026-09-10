from pydantic import BaseModel, Field, field_validator


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)

    @field_validator("refresh_token")
    @classmethod
    def refresh_token_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("refresh_token cannot be empty")
        return stripped


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900
