from app.features.auth.exceptions import (
    EmailAlreadyRegisteredError,
    UnVerifiedUserError,
)
from app.features.users.models.user import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def ensure_email_is_available(existing_user: User | None) -> None:
    if existing_user is not None:
        raise EmailAlreadyRegisteredError(existing_user)


def ensure_user_can_login(user: User) -> None:
    if not user.is_email_verified:
        raise UnVerifiedUserError
