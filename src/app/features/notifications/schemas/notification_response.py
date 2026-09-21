from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.features.notifications.domain.enums import (
    NotificationStatus,
    NotificationType,
)


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    message: str
    type: NotificationType
    status: NotificationStatus
    is_read: bool
    read_at: datetime | None
    data: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class PaginatedNotificationsResponse(BaseModel):
    items: list[NotificationResponse]
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    unread_count: int = Field(..., ge=0)


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int = Field(..., ge=0)
