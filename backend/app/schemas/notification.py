from datetime import datetime

from pydantic import BaseModel

from app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    id: str
    type: NotificationType
    title: str
    message: str
    donation_id: str | None
    is_read: bool
    created_at: datetime
    read_at: datetime | None

    model_config = {"from_attributes": True}


class PaginatedNotificationsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[NotificationResponse]


class UnreadCountResponse(BaseModel):
    unread_count: int


class MarkAllReadResponse(BaseModel):
    updated: int
