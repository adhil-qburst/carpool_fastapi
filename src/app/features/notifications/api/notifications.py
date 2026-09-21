from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.notifications.domain.enums import (
    NotificationStatus,
    NotificationType,
)
from app.features.notifications.exceptions import (
    InvalidPaginationError,
    NotificationForbiddenError,
    NotificationNotFoundError,
)
from app.features.notifications.schemas.notification_response import (
    NotificationResponse,
    NotificationUnreadCountResponse,
    PaginatedNotificationsResponse,
)
from app.features.notifications.services.get_notification import (
    get_notification,
)
from app.features.notifications.services.get_unread_count import (
    get_user_unread_count,
)
from app.features.notifications.services.list_notifications import (
    list_user_notifications,
)

router = APIRouter()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedNotificationsResponse,
)
def list_notifications(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    is_read: bool | None = Query(default=None),
    status_filter: NotificationStatus | None = Query(default=None, alias="status"),
    notification_type: NotificationType | None = Query(default=None, alias="type"),
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> PaginatedNotificationsResponse:
    offset = (page - 1) * limit
    try:
        items, total, unread_count = list_user_notifications(
            session=db,
            user_id=current_user_id,
            is_read=is_read,
            status=status_filter,
            type=notification_type,
            limit=limit,
            offset=offset,
        )
        return PaginatedNotificationsResponse(
            items=items,
            page=page,
            limit=limit,
            total=total,
            unread_count=unread_count,
        )
    except InvalidPaginationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc


@router.get(
    "/unread-count",
    status_code=status.HTTP_200_OK,
    response_model=NotificationUnreadCountResponse,
)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> NotificationUnreadCountResponse:
    count = get_user_unread_count(
        session=db,
        user_id=current_user_id,
    )
    return NotificationUnreadCountResponse(unread_count=count)


@router.get(
    "/{notification_id}",
    status_code=status.HTTP_200_OK,
    response_model=NotificationResponse,
)
def get_notification_by_id(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
) -> NotificationResponse:
    try:
        return get_notification(
            session=db,
            notification_id=notification_id,
            user_id=current_user_id,
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.detail,
        ) from exc
    except NotificationForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.detail,
        ) from exc
