from app.core.exceptions import AppError
from app.features.users.models.user import User


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


class InvalidEmailVerificationTokenError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "The verification link is invalid, expired, or has already been used.",
            "INVALID_EMAIL_VERIFICATION_TOKEN",
        )


class InvalidCredentialError(AppError):
    def __init__(self):
        super().__init__("Invalid email or password", "INVALID_CREDENTIALS")


class UnVerifiedUserError(AppError):
    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email
        super().__init__("Please verify your email before login.", "UNVERIFIED_USER")


class EmailNotFoundError(AppError):
    def __init__(self):
        super().__init__("User not found with this email.", "USER_NOT_FOUND")


class UserDisabledError(AppError):
    def __init__(self):
        super()._init__("User account is disabled.", "USER_DISABLED")


class RegisteredUserError(AppError):
    def __init__(self):
        super().__init__(
            "User is already registered. Please login with your email.",
            "REGISTERED_USER",
        )
