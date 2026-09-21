from uuid import UUID

from app.core.exceptions import AppError


class NotificationNotFoundError(AppError):
    def __init__(self, notification_id: UUID | None = None) -> None:
        self.notification_id = notification_id
        super().__init__("Notification not found.", "NOTIFICATION_NOT_FOUND")


class NotificationForbiddenError(AppError):
    def __init__(
        self,
        notification_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> None:
        self.notification_id = notification_id
        self.user_id = user_id
        super().__init__(
            "You do not have permission to access this notification.",
            "NOTIFICATION_ACCESS_DENIED",
        )


class InvalidPaginationError(AppError):
    def __init__(self, limit: int, offset: int) -> None:
        self.limit = limit
        self.offset = offset
        super().__init__(
            "Limit must be greater than 0 and offset must be non-negative.",
            "INVALID_PAGINATION",
        )
