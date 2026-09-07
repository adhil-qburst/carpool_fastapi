from app.core.exceptions import EmailAlreadyRegisteredError
from app.models.user import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def ensure_email_is_available(existing_user: User | None) -> None:
    if existing_user is not None:
        raise EmailAlreadyRegisteredError(existing_user)
