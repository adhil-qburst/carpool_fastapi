from enum import StrEnum


class NotificationType(StrEnum):
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING_REQUEST = "booking_request"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_REJECTED = "booking_rejected"
    TRIP_CANCELLED = "trip_cancelled"
    TRIP_UPDATED = "trip_updated"
    SYSTEM = "system"


class NotificationStatus(StrEnum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
