from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security.verification_token import hash_token
from app.features.auth.exceptions import InvalidEmailVerificationTokenError
from app.features.users.domain.enums import UserStatus
from app.features.users.repositories.email_verification_tokens import (
    get_email_verification_token_repo,
)
from app.features.users.repositories.users import get_user_repo


def verify_email(session: Session, token: UUID) -> None:
    """Verify an email address and consume its token in one transaction."""
    user_repo = get_user_repo()
    email_verification_token_repo = get_email_verification_token_repo()
    with session.begin():
        verification_token = (
            email_verification_token_repo.get_active_by_hash_for_update(
                session,
                hash_token(str(token)),
            )
        )
        if verification_token is None:
            raise InvalidEmailVerificationTokenError()

        user = user_repo.get_by_id(session, verification_token.user_id)
        if user is None:
            raise InvalidEmailVerificationTokenError()

        user.is_email_verified = True
        user.status = UserStatus.ACTIVE
        verification_token.used_at = func.now()
