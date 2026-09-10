from pydantic import BaseModel


class AuthToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None


class RefreshedToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
