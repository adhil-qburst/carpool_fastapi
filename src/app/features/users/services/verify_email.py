from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidEmailVerificationTokenError
from app.core.security import hash_token
from app.features.users.domain.enums import UserStatus
from app.features.users.repositories import email_verification_tokens as token_repo
from app.features.users.repositories import users as users_repo


def verify_email(session: Session, token: UUID) -> None:
    """Verify an email address and consume its token in one transaction."""
    with session.begin():
        verification_token = token_repo.get_active_by_hash_for_update(
            session,
            hash_token(str(token)),
        )
        if verification_token is None:
            raise InvalidEmailVerificationTokenError()

        user = users_repo.get_by_id(session, verification_token.user_id)
        if user is None:
            raise InvalidEmailVerificationTokenError()

        user.is_email_verified = True
        user.status = UserStatus.ACTIVE
        verification_token.used_at = func.now()
