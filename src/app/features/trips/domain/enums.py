from enum import StrEnum


class TripStatus(StrEnum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    DELETED = "deleted"

