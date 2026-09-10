from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.security.jwt import JWTService

http_bearer = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    settings: Settings = Depends(get_settings),
) -> UUID:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    jwt_service = JWTService(
        secret_key=settings.jwt_secret,
        refresh_secret_key=settings.jwt_refresh_secret,
        algorithm=settings.jwt_algorithm,
    )

    try:
        payload = jwt_service.validate_access_token(credentials.credentials)
        return UUID(str(payload["sub"]))
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
