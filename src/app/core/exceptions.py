from app.features.users.models.user import User


class AppError(Exception):
    def __init__(self, detail: str, code: str | None = None) -> None:
        self.detail = detail
        self.code = code
        super().__init__(detail)
