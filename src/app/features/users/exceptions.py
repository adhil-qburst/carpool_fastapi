from app.core.exceptions import AppError


class UserNotFoundError(AppError):
    def __init__(self):
        super().__init__("User not found in the server", "USER_NOT_FOUND")
