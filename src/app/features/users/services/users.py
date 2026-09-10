from uuid import UUID

from sqlalchemy.orm import Session

from app.features.users.exceptions import UserNotFoundError
from app.features.users.models.user import User
from app.features.users.repositories.users import get_user_repo


def get_current_user(session: Session, user_id: UUID) -> User:
    user_repo = get_user_repo()

    user = user_repo.get_by_id(user_id=user_id, session=session)

    if user is None:
        raise UserNotFoundError

    return user
