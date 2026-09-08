from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security.password import hash_password
from app.features.auth.exceptions import EmailAlreadyRegisteredError, EmailDeliveryError, RegisteredUserError
from app.features.auth.schemas.register import RegisterRequest
from app.features.auth.services.send_email_token import send_email_token
from app.features.users.domain.rules import ensure_email_is_available, normalize_email
from app.features.users.repositories.users import get_user_repo


def register_user(
    session: Session,
    payload: RegisterRequest,
    *,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()

    email = normalize_email(payload.email)
    user_repo = get_user_repo()

    try:
        ensure_email_is_available(user_repo.get_by_email(session, email))
        user = user_repo.create_user(
            session,
            name=payload.name.strip(),
            email=email,
            password_hash=hash_password(payload.password),
            roles=payload.roles,
        )
    except EmailAlreadyRegisteredError as exc:
        
        if exc.user.is_email_verified:
            raise RegisteredUserError
        
        user = exc.user
        user.name = payload.name
        user.password_hash = hash_password(payload.password)
        user.roles = payload.roles

    try:
        send_email_token(
            session=session, settings=settings, user_id=user.id, email=user.email
        )
    except EmailDeliveryError:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise EmailDeliveryError from exc

    session.commit()
