from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.donation import Donation
from app.models.notification import Notification, NotificationType
from app.models.user import User


def actor_display_name(user: User | None) -> str:
    if user is None:
        return "FoodBridge user"
    return user.organization_name or user.name


def create_notification_once(
    db: Session,
    *,
    user_id: str,
    notification_type: NotificationType,
    title: str,
    message: str,
    donation_id: str | None = None,
    commit: bool = True,
) -> Notification:
    existing = get_existing_notification(db, user_id, notification_type, donation_id)
    if existing is not None:
        return existing

    notification = Notification(
        user_id=user_id,
        type=notification_type.value,
        title=title,
        message=message,
        donation_id=donation_id,
    )
    db.add(notification)
    try:
        if commit:
            db.commit()
            db.refresh(notification)
        else:
            db.flush()
    except IntegrityError:
        db.rollback()
        existing = get_existing_notification(db, user_id, notification_type, donation_id)
        if existing is not None:
            return existing
        raise
    return notification


def get_existing_notification(
    db: Session,
    user_id: str,
    notification_type: NotificationType,
    donation_id: str | None,
) -> Notification | None:
    statement = select(Notification).where(
        Notification.user_id == user_id,
        Notification.type == notification_type.value,
        Notification.donation_id == donation_id,
    )
    return db.scalar(statement)


def notify_donation_accepted(db: Session, donation: Donation, accepted_by: User) -> None:
    receiver_name = actor_display_name(accepted_by)
    create_notification_once(
        db,
        user_id=donation.donor_id,
        notification_type=NotificationType.DONATION_ACCEPTED,
        title="Donation Accepted",
        message=f"Your donation '{donation.food_name}' was accepted by {receiver_name}.",
        donation_id=donation.id,
    )
    create_notification_once(
        db,
        user_id=accepted_by.id,
        notification_type=NotificationType.DONATION_ACCEPTED,
        title="Donation Accepted",
        message=f"You accepted '{donation.food_name}'.",
        donation_id=donation.id,
    )


def notify_donation_collected(db: Session, donation: Donation, receiver: User) -> None:
    create_notification_once(
        db,
        user_id=donation.donor_id,
        notification_type=NotificationType.DONATION_COLLECTED,
        title="Food Collected",
        message=f"Your donation '{donation.food_name}' has been collected.",
        donation_id=donation.id,
    )
    create_notification_once(
        db,
        user_id=receiver.id,
        notification_type=NotificationType.DONATION_COLLECTED,
        title="Food Collected",
        message=f"'{donation.food_name}' marked as collected.",
        donation_id=donation.id,
    )


def notify_donation_distributed(db: Session, donation: Donation, receiver: User) -> None:
    create_notification_once(
        db,
        user_id=donation.donor_id,
        notification_type=NotificationType.DONATION_DISTRIBUTED,
        title="Donation Distributed",
        message=f"Your donation '{donation.food_name}' has been distributed successfully.",
        donation_id=donation.id,
    )
    create_notification_once(
        db,
        user_id=receiver.id,
        notification_type=NotificationType.DONATION_DISTRIBUTED,
        title="Donation Distributed",
        message=f"'{donation.food_name}' marked as distributed.",
        donation_id=donation.id,
    )


def notify_donation_expired(db: Session, donation: Donation, commit: bool = False) -> None:
    create_notification_once(
        db,
        user_id=donation.donor_id,
        notification_type=NotificationType.DONATION_EXPIRED,
        title="Donation Expired",
        message=f"Your donation '{donation.food_name}' expired before being accepted.",
        donation_id=donation.id,
        commit=commit,
    )


def list_user_notifications(
    db: Session,
    *,
    user_id: str,
    page: int,
    page_size: int,
    unread_only: bool = False,
) -> tuple[int, list[Notification]]:
    conditions = [Notification.user_id == user_id]
    if unread_only:
        conditions.append(Notification.is_read.is_(False))

    total = db.scalar(select(func.count()).select_from(Notification).where(*conditions)) or 0
    statement = (
        select(Notification)
        .where(*conditions)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return total, list(db.scalars(statement))


def get_unread_count(db: Session, user_id: str) -> int:
    return db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    ) or 0


def get_user_notification(db: Session, notification_id: str, user_id: str) -> Notification | None:
    return db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )


def mark_notification_read(db: Session, notification: Notification) -> Notification:
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.add(notification)
        db.commit()
        db.refresh(notification)
    return notification


def mark_all_notifications_read(db: Session, user_id: str) -> int:
    now = datetime.now(timezone.utc)
    statement = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True, read_at=now)
    )
    result = db.execute(statement.execution_options(synchronize_session=False))
    db.commit()
    return result.rowcount or 0
