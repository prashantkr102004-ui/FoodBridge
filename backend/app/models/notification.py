import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User, utc_now


class NotificationType(str, Enum):
    DONATION_ACCEPTED = "DONATION_ACCEPTED"
    DONATION_COLLECTED = "DONATION_COLLECTED"
    DONATION_DISTRIBUTED = "DONATION_DISTRIBUTED"
    DONATION_CANCELLED = "DONATION_CANCELLED"
    DONATION_EXPIRED = "DONATION_EXPIRED"
    SYSTEM = "SYSTEM"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("user_id", "type", "donation_id", name="uq_notification_user_type_donation"),
        Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    donation_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("donations.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(foreign_keys=[user_id])
