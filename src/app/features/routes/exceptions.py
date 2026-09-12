from uuid import UUID

from app.core.exceptions import AppError


class RouteNotFoundError(AppError):
    def __init__(self, route_id: UUID | None = None) -> None:
        self.route_id = route_id
        super().__init__("Route not found.", "ROUTE_NOT_FOUND")


class RouteStopNotFoundError(AppError):
    def __init__(self, stop_id: UUID | None = None) -> None:
        self.stop_id = stop_id
        super().__init__("Route stop not found.", "ROUTE_STOP_NOT_FOUND")


class RouteForbiddenError(AppError):
    def __init__(
        self, route_id: UUID | None = None, user_id: UUID | None = None
    ) -> None:
        self.route_id = route_id
        self.user_id = user_id
        super().__init__(
            "You do not have permission to access or modify this route.",
            "ROUTE_ACCESS_DENIED",
        )


class RouteNameAlreadyExistsError(AppError):
    def __init__(self, name: str, driver_id: UUID | None = None) -> None:
        self.name = name
        self.driver_id = driver_id
        super().__init__(
            f"A route named '{name}' already exists for this driver.",
            "ROUTE_NAME_ALREADY_EXISTS",
        )


class IdenticalSourceDestinationError(AppError):
    def __init__(self, location_id: UUID | None = None) -> None:
        self.location_id = location_id
        super().__init__(
            "Source and destination locations cannot be identical.",
            "IDENTICAL_SOURCE_DESTINATION",
        )


class DuplicateStopLocationError(AppError):
    def __init__(
        self, location_id: UUID | None = None, route_id: UUID | None = None
    ) -> None:
        self.location_id = location_id
        self.route_id = route_id
        super().__init__(
            "This location is already a stop on this route.",
            "DUPLICATE_STOP_LOCATION",
        )


class InvalidStopSequenceError(AppError):
    def __init__(self, sequence: int) -> None:
        self.sequence = sequence
        super().__init__(
            f"Invalid stop sequence '{sequence}'.",
            "INVALID_STOP_SEQUENCE",
        )


class DuplicateStopSequenceError(AppError):
    def __init__(self, sequence: int | None = None) -> None:
        self.sequence = sequence
        detail = (
            f"Duplicate stop sequence '{sequence}'."
            if sequence is not None
            else "Duplicate stop sequence."
        )
        super().__init__(detail, "DUPLICATE_STOP_SEQUENCE")


class StopsDoNotBelongToSameRouteError(AppError):
    def __init__(
        self, stop_1_id: UUID | None = None, stop_2_id: UUID | None = None
    ) -> None:
        self.stop_1_id = stop_1_id
        self.stop_2_id = stop_2_id
        super().__init__(
            "Both stops must belong to the same route to be swapped.",
            "STOPS_DIFFERENT_ROUTES",
        )


class CannotSwapSameStopError(AppError):
    def __init__(self, stop_id: UUID | None = None) -> None:
        self.stop_id = stop_id
        super().__init__(
            "Cannot swap a stop with itself.",
            "CANNOT_SWAP_SAME_STOP",
        )


class InvalidPaginationError(AppError):
    def __init__(self, limit: int, offset: int) -> None:
        self.limit = limit
        self.offset = offset
        super().__init__(
            "Limit must be greater than 0 and offset must be non-negative.",
            "INVALID_PAGINATION",
        )
