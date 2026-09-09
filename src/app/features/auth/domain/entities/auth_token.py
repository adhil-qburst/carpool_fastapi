from pydantic import BaseModel


class AuthToken(BaseModel):
    access_token: str
    refresh_token: str
