from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security.jwt import JWTService
from app.features.auth.domain.entities.auth_token import RefreshedToken
from app.features.auth.domain.rules import ensure_user_is_active
from app.features.auth.exceptions import InvalidRefreshTokenError, UnVerifiedUserError
from app.features.users.models.user import User
from app.features.users.repositories.users import get_user_repo


def refresh_access_token(
    session: Session,
    refresh_token: str,
    *,
    settings: Settings | None = None,
) -> RefreshedToken:
    settings = settings or get_settings()

    jwt_service = JWTService(
        secret_key=settings.jwt_secret,
        refresh_secret_key=settings.jwt_refresh_secret,
        algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
    )

    try:
        try:
            payload = jwt_service.validate_refresh_token(refresh_token)
            user_id = UUID(str(payload.get("sub")))
        except (ValueError, TypeError) as exc:
            raise InvalidRefreshTokenError() from exc

        user_repo = get_user_repo()
        user: User | None = user_repo.get_by_id(session, user_id)
        if user is None:
            raise InvalidRefreshTokenError()

        ensure_user_is_active(user)

        if not user.is_email_verified:
            raise UnVerifiedUserError(user_id=user.id, email=user.email)

        access_token = jwt_service.create_access_token(user_id=user.id)
        expires_in = jwt_service.access_token_expire_minutes * 60

        return RefreshedToken(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        )
    except Exception:
        session.rollback()
        raise
