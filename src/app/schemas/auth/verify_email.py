from pydantic import BaseModel


class VerifyEmailResponse(BaseModel):
    message: str
