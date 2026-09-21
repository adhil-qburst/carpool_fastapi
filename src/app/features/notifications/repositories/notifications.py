from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.notifications.domain.enums import (
    NotificationStatus,
    NotificationType,
)
from app.features.notifications.models.notification import Notification


class NotificationRepo:
    def create(
        self,
        session: Session,
        *,
        user_id: UUID,
        title: str,
        message: str,
        type: NotificationType = NotificationType.SYSTEM,
        status: NotificationStatus = NotificationStatus.UNREAD,
        is_read: bool = False,
        read_at: datetime | None = None,
        data: dict[str, Any] | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            status=status,
            is_read=is_read,
            read_at=read_at,
            data=data,
        )
        session.add(notification)
        session.flush()
        return notification

    def get_by_id(
        self,
        session: Session,
        notification_id: UUID,
    ) -> Notification | None:
        return session.get(Notification, notification_id)

    def get_by_id_for_update(
        self,
        session: Session,
        notification_id: UUID,
    ) -> Notification | None:
        return session.scalar(
            select(Notification)
            .where(Notification.id == notification_id)
            .with_for_update()
        )

    def list_by_user(
        self,
        session: Session,
        *,
        user_id: UUID,
        is_read: bool | None = None,
        status: NotificationStatus | None = None,
        type: NotificationType | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        base_stmt = select(Notification).where(Notification.user_id == user_id)
        count_stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id)
        )

        if is_read is not None:
            base_stmt = base_stmt.where(Notification.is_read == is_read)
            count_stmt = count_stmt.where(Notification.is_read == is_read)

        if status is not None:
            base_stmt = base_stmt.where(Notification.status == status)
            count_stmt = count_stmt.where(Notification.status == status)

        if type is not None:
            base_stmt = base_stmt.where(Notification.type == type)
            count_stmt = count_stmt.where(Notification.type == type)

        total = session.scalar(count_stmt) or 0
        items = list(
            session.scalars(
                base_stmt.order_by(Notification.created_at.desc())
                .limit(limit)
                .offset(offset)
            ).all()
        )
        return items, total

    def get_unread_count(
        self,
        session: Session,
        *,
        user_id: UUID,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return session.scalar(stmt) or 0


def get_notification_repo() -> NotificationRepo:
    return NotificationRepo()
