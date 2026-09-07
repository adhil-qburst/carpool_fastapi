from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.email_verification_token import EmailVerificationToken


def create(
    session: Session,
    *,
    user_id: UUID,
    token_hash: str,
    expires_at: datetime,
) -> EmailVerificationToken:
    record = EmailVerificationToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    session.add(record)
    session.flush()
    return record
