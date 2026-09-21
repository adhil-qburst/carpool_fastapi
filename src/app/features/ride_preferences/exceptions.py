from uuid import UUID

from app.core.exceptions import AppError


class RidePreferenceNotFoundError(AppError):
    def __init__(self, preference_id: UUID | None = None) -> None:
        self.preference_id = preference_id
        super().__init__("Ride preference not found.", "RIDE_PREFERENCE_NOT_FOUND")


class RidePreferenceForbiddenError(AppError):
    def __init__(
        self,
        preference_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> None:
        self.preference_id = preference_id
        self.user_id = user_id
        super().__init__(
            "You do not have permission to access or modify this ride preference.",
            "RIDE_PREFERENCE_ACCESS_DENIED",
        )


class SameLocationRidePreferenceError(AppError):
    def __init__(
        self,
        source_location_id: UUID | None = None,
        destination_location_id: UUID | None = None,
    ) -> None:
        self.source_location_id = source_location_id
        self.destination_location_id = destination_location_id
        super().__init__(
            "Source and destination locations must be different.",
            "SAME_SOURCE_AND_DESTINATION_LOCATION",
        )


class InvalidSeatsNeededError(AppError):
    def __init__(self, seats_needed: int | None = None) -> None:
        self.seats_needed = seats_needed
        super().__init__(
            "Seats needed must be at least 1.",
            "INVALID_SEATS_NEEDED",
        )


class InvalidRidePreferenceLabelError(AppError):
    def __init__(self, label: str | None = None) -> None:
        self.label = label
        super().__init__(
            "Ride preference label must not exceed 100 characters.",
            "INVALID_RIDE_PREFERENCE_LABEL",
        )


class DuplicateRidePreferenceError(AppError):
    def __init__(
        self,
        source_location_id: UUID | None = None,
        destination_location_id: UUID | None = None,
    ) -> None:
        self.source_location_id = source_location_id
        self.destination_location_id = destination_location_id
        super().__init__(
            "An active ride preference between these locations already exists.",
            "DUPLICATE_RIDE_PREFERENCE",
        )


class InvalidPaginationError(AppError):
    def __init__(self, limit: int, offset: int) -> None:
        self.limit = limit
        self.offset = offset
        super().__init__(
            "Limit must be greater than 0 and offset must be non-negative.",
            "INVALID_PAGINATION",
        )
