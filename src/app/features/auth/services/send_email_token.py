from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.email import send_verification_email
from app.core.security.verification_token import generate_verification_token, hash_token
from app.features.users.repositories import email_verification_tokens as token_repo
from app.features.users.repositories import users as users_repo


def send_email_token(session: Session, settings: Settings, user_id: str, email: str):

    raw_token = generate_verification_token()
    token_repo.create(
        session,
        user_id=user_id,
        token_hash=hash_token(raw_token),
        expires_at=users_repo.verification_expiry(
            settings.email_verification_expire_hours
        ),
    )
    send_verification_email(email, raw_token, settings=settings)
