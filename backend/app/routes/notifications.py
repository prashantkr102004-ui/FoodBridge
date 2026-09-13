from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    MarkAllReadResponse,
    NotificationResponse,
    PaginatedNotificationsResponse,
    UnreadCountResponse,
)
from app.services.notification_service import (
    get_unread_count,
    get_user_notification,
    list_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=PaginatedNotificationsResponse)
def get_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedNotificationsResponse:
    total, notifications = list_user_notifications(
        db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )
    return PaginatedNotificationsResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[NotificationResponse.model_validate(notification) for notification in notifications],
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_notification_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UnreadCountResponse:
    return UnreadCountResponse(unread_count=get_unread_count(db, current_user.id))


@router.post("/read-all", response_model=MarkAllReadResponse)
def read_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MarkAllReadResponse:
    return MarkAllReadResponse(updated=mark_all_notifications_read(db, current_user.id))


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def read_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notification:
    notification = get_user_notification(db, notification_id, current_user.id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return mark_notification_read(db, notification)
