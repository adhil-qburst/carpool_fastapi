from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.users.enums import UserRole, UserStatus
from app.models.user import User


def get_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))


def create_user(
    session: Session,
    *,
    name: str,
    email: str,
    password_hash: str,
    roles: list[UserRole],
) -> User:
    user = User(
        name=name,
        email=email,
        password_hash=password_hash,
        roles=list(roles),
        status=UserStatus.PENDING.value,
        is_email_verified=False,
    )
    session.add(user)
    session.flush()
    return user


def verification_expiry(hours: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)
