from app.features.auth.exceptions import UserDisabledError
from app.features.users.domain.enums import UserStatus
from app.features.users.models.user import User


def ensure_user_is_active(user: User) -> None:
    if user.status is UserStatus.DISABLED:
        raise UserDisabledError()
