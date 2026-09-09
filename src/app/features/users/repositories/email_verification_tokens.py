from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.users.models.email_verification_token import EmailVerificationToken


class EmailVerificationTokenRepo:
    def create(
        self,
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

    def get_active_by_hash_for_update(
        self,
        session: Session,
        token_hash: str,
    ) -> EmailVerificationToken | None:
        return session.scalar(
            select(EmailVerificationToken)
            .where(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.used_at.is_(None),
                EmailVerificationToken.expires_at > func.now(),
            )
            .with_for_update()
        )


def get_email_verification_token_repo() -> EmailVerificationTokenRepo:
    return EmailVerificationTokenRepo()
