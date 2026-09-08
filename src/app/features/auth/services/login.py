from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security.jwt import JWTService
from app.core.security.password import verify_password
from app.features.auth.domain.entities.auth_token import AuthToken
from app.features.auth.exceptions import (
    EmailNotFoundError,
    InvalidCredentialError,
    UnVerifiedUserError,
    UserDisabledError,
)
from app.features.auth.services.send_email_token import send_email_token
from app.features.users.domain.enums import UserStatus
from app.features.users.models.user import User
from app.features.users.repositories import users as UserRepo


def login_with_email_password(
    session: Session,
    email: str,
    password: str,
    *,
    settings: Settings | None = None,
) -> AuthToken:
    settings = settings or get_settings()
    try:

        user: User = UserRepo.get_by_email(session=session, email=email)

        if user is None:
            raise EmailNotFoundError

        if not verify_password(password=password, password_hash=user.password_hash):
            raise InvalidCredentialError

        if user.status is UserStatus.DISABLED:
            raise UserDisabledError

        if not user.is_email_verified:
            raise UnVerifiedUserError(user_id=user.id, email=user.email)

        jwt_service = JWTService(
            secret_key=settings.jwt_secret,
            refresh_secret_key=settings.jwt_refresh_secret,
            algorithm=settings.jwt_algorithm,
            access_token_expire_minutes=15,
            refresh_token_expire_days=7,
        )

        access_token = jwt_service.create_access_token(user_id=user.id)

        refresh_token = jwt_service.create_refresh_token(user_id=user.id)

        user.last_login = datetime.now(timezone.utc)

        session.commit()

        return AuthToken(access_token=access_token, refresh_token=refresh_token)
    except UnVerifiedUserError as exc:
        send_email_token(
            session=session, settings=settings, email=exc.email, user_id=exc.user_id
        )
        raise
    except Exception:
        session.rollback()
        raise
