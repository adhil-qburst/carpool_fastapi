from enum import StrEnum


class UserRole(StrEnum):
    DRIVER = "driver"
    RIDER = "rider"

class UserStatus(StrEnum):
    PENDING = 'pending'
    ACTIVE = 'active'
    DISABLED = 'disabled'
