from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.email import send_verification_email
from app.core.exceptions import EmailAlreadyRegisteredError, EmailDeliveryError
from app.core.security import generate_verification_token, hash_password, hash_token
from app.domain.users.rules import ensure_email_is_available, normalize_email
from app.repositories import email_verification_tokens as token_repo
from app.repositories import users as users_repo
from app.schemas.auth.register import RegisterRequest

SendVerificationEmail = Callable[[str, str], None]


def register_user(
    session: Session,
    payload: RegisterRequest,
    *,
    send_email: SendVerificationEmail | None = None,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    email = normalize_email(payload.email)
    try:
        ensure_email_is_available(users_repo.get_by_email(session, email))
        user = users_repo.create_user(
            session,
            name=payload.name.strip(),
            email=email,
            password_hash=hash_password(payload.password),
            roles=payload.roles,
        )
    except EmailAlreadyRegisteredError as exc:
        user = exc.user
        user.name = payload.name
        user.password_hash = hash_password(payload.password)
        user.roles = payload.roles

    raw_token = generate_verification_token()
    token_repo.create(
        session,
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=users_repo.verification_expiry(
            settings.email_verification_expire_hours
        ),
    )

    dispatch = send_email or (
        lambda to, token: send_verification_email(to, token, settings=settings)
    )
    try:
        dispatch(email, raw_token)
    except EmailDeliveryError:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise EmailDeliveryError from exc

    session.commit()
