from app.models.user import User


class AppError(Exception):
    def __init__(self, detail: str, code: str | None = None) -> None:
        self.detail = detail
        self.code = code
        super().__init__(detail)


class EmailAlreadyRegisteredError(AppError):
    def __init__(self, user: User) -> None:
        self.user: User = user
        super().__init__(
            "An account with this email already exists.",
            "EMAIL_ALREADY_REGISTERED",
        )


class EmailDeliveryError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Could not send the verification email. Please try again.",
            "EMAIL_DELIVERY_FAILED",
        )
