from calendar import monthrange
from datetime import date, datetime, time, timezone

from sqlalchemy import extract, func, or_, select
from sqlalchemy.orm import Session

from app.models.donation import Donation, DonationStatus
from app.models.user import User, UserRole
from app.schemas.analytics import (
    AdminAnalyticsResponse,
    DonorAnalyticsResponse,
    ImpactDonationItem,
    MonthlyActivityItem,
    ReceiverAnalyticsResponse,
)

TERMINAL_STATUSES = [
    DonationStatus.DISTRIBUTED.value,
    DonationStatus.CANCELLED.value,
    DonationStatus.EXPIRED.value,
]
ACTIVE_STATUSES = [
    DonationStatus.AVAILABLE.value,
    DonationStatus.ACCEPTED.value,
    DonationStatus.COLLECTED.value,
]


def date_range_conditions(start_date: date | None, end_date: date | None) -> list:
    conditions = []
    if start_date is not None:
        conditions.append(Donation.created_at >= datetime.combine(start_date, time.min, tzinfo=timezone.utc))
    if end_date is not None:
        conditions.append(Donation.created_at <= datetime.combine(end_date, time.max, tzinfo=timezone.utc))
    return conditions


def count_donations(db: Session, *conditions) -> int:
    return db.scalar(select(func.count(Donation.id)).where(*conditions)) or 0


def count_users(db: Session, *conditions) -> int:
    return db.scalar(select(func.count(User.id)).where(*conditions)) or 0


def grouped_counts(db: Session, column, *conditions) -> dict[str, int]:
    statement = select(column, func.count()).where(*conditions).group_by(column)
    return {str(key): count for key, count in db.execute(statement).all()}


def quantity_by_unit(db: Session, *conditions) -> dict[str, float]:
    statement = select(Donation.quantity_unit, func.sum(Donation.quantity)).where(*conditions).group_by(Donation.quantity_unit)
    return {unit: float(total or 0) for unit, total in db.execute(statement).all()}


def success_rate(distributed: int, terminal_total: int) -> float:
    if terminal_total == 0:
        return 0.0
    return round((distributed / terminal_total) * 100, 2)


def completion_rate(distributed: int, total_accepted: int) -> float:
    if total_accepted == 0:
        return 0.0
    return round((distributed / total_accepted) * 100, 2)


def month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def add_months(value: date, months: int) -> date:
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def default_month_window() -> tuple[date, date]:
    today = datetime.now(timezone.utc).date()
    start = add_months(month_start(today), -5)
    return start, today


def build_month_keys(start_date: date, end_date: date) -> list[str]:
    keys = []
    cursor = month_start(start_date)
    end = month_start(end_date)
    while cursor <= end:
        keys.append(cursor.strftime("%Y-%m"))
        cursor = add_months(cursor, 1)
    return keys


def monthly_activity(
    db: Session,
    *conditions,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[MonthlyActivityItem]:
    if start_date is None or end_date is None:
        default_start, default_end = default_month_window()
        start_date = start_date or default_start
        end_date = end_date or default_end

    created_counts = grouped_month_counts(db, Donation.created_at, *conditions, *date_range_conditions(start_date, end_date))
    distributed_conditions = [
        *conditions,
        Donation.status == DonationStatus.DISTRIBUTED.value,
        Donation.distributed_at.is_not(None),
        Donation.distributed_at >= datetime.combine(start_date, time.min, tzinfo=timezone.utc),
        Donation.distributed_at <= datetime.combine(end_date, time.max, tzinfo=timezone.utc),
    ]
    distributed_counts = grouped_month_counts(db, Donation.distributed_at, *distributed_conditions)

    return [
        MonthlyActivityItem(
            month=month,
            created=created_counts.get(month, 0),
            distributed=distributed_counts.get(month, 0),
        )
        for month in build_month_keys(start_date, end_date)
    ]


def grouped_month_counts(db: Session, date_column, *conditions) -> dict[str, int]:
    year_part = extract("year", date_column)
    month_part = extract("month", date_column)
    statement = select(year_part, month_part, func.count()).where(*conditions).group_by(year_part, month_part)
    counts: dict[str, int] = {}
    for year, month, count in db.execute(statement).all():
        counts[f"{int(year):04d}-{int(month):02d}"] = count
    return counts


def recent_impact(db: Session, *conditions, limit: int = 5) -> list[ImpactDonationItem]:
    statement = (
        select(Donation)
        .where(
            *conditions,
            Donation.status == DonationStatus.DISTRIBUTED.value,
            Donation.distributed_at.is_not(None),
        )
        .order_by(Donation.distributed_at.desc())
        .limit(limit)
    )
    return [
        ImpactDonationItem(
            id=donation.id,
            food_name=donation.food_name,
            quantity=donation.quantity,
            quantity_unit=donation.quantity_unit,
            distributed_at=donation.distributed_at.date() if donation.distributed_at else None,
        )
        for donation in db.scalars(statement)
    ]


def get_donor_analytics(db: Session, donor_id: str) -> DonorAnalyticsResponse:
    own = Donation.donor_id == donor_id
    distributed = count_donations(db, own, Donation.status == DonationStatus.DISTRIBUTED.value)
    terminal_total = count_donations(db, own, Donation.status.in_(TERMINAL_STATUSES))

    return DonorAnalyticsResponse(
        total_donations=count_donations(db, own),
        distributed_donations=distributed,
        active_donations=count_donations(db, own, Donation.status.in_(ACTIVE_STATUSES)),
        cancelled_donations=count_donations(db, own, Donation.status == DonationStatus.CANCELLED.value),
        expired_donations=count_donations(db, own, Donation.status == DonationStatus.EXPIRED.value),
        success_rate=success_rate(distributed, terminal_total),
        quantity_by_unit=quantity_by_unit(db, own),
        distributed_quantity_by_unit=quantity_by_unit(db, own, Donation.status == DonationStatus.DISTRIBUTED.value),
        food_type_breakdown=grouped_counts(db, Donation.food_type, own),
        monthly_activity=monthly_activity(db, own),
        recent_impact=recent_impact(db, own),
    )


def get_receiver_analytics(db: Session, receiver_id: str) -> ReceiverAnalyticsResponse:
    own = Donation.accepted_by_user_id == receiver_id
    distributed = count_donations(db, own, Donation.status == DonationStatus.DISTRIBUTED.value)
    total_accepted = count_donations(db, own)

    return ReceiverAnalyticsResponse(
        total_accepted=total_accepted,
        currently_accepted=count_donations(db, own, Donation.status == DonationStatus.ACCEPTED.value),
        collected=count_donations(db, own, Donation.status == DonationStatus.COLLECTED.value),
        distributed=distributed,
        completion_rate=completion_rate(distributed, total_accepted),
        quantity_rescued_by_unit=quantity_by_unit(db, own, Donation.status == DonationStatus.DISTRIBUTED.value),
        food_type_breakdown=grouped_counts(db, Donation.food_type, own),
        monthly_activity=monthly_activity(db, own),
        recent_impact=recent_impact(db, own),
    )


def get_admin_analytics(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
) -> AdminAnalyticsResponse:
    conditions = date_range_conditions(start_date, end_date)
    distributed = count_donations(db, *conditions, Donation.status == DonationStatus.DISTRIBUTED.value)
    terminal_total = count_donations(db, *conditions, Donation.status.in_(TERMINAL_STATUSES))

    return AdminAnalyticsResponse(
        total_users=count_users(db),
        total_donations=count_donations(db, *conditions),
        total_distributed=distributed,
        total_cancelled=count_donations(db, *conditions, Donation.status == DonationStatus.CANCELLED.value),
        total_expired=count_donations(db, *conditions, Donation.status == DonationStatus.EXPIRED.value),
        distribution_success_rate=success_rate(distributed, terminal_total),
        users_by_role=grouped_counts(db, User.role),
        donations_by_status=grouped_counts(db, Donation.status, *conditions),
        quantity_distributed_by_unit=quantity_by_unit(db, *conditions, Donation.status == DonationStatus.DISTRIBUTED.value),
        food_type_breakdown=grouped_counts(db, Donation.food_type, *conditions),
        monthly_donation_activity=monthly_activity(db, *conditions, start_date=start_date, end_date=end_date),
    )


def export_impact_rows(db: Session, status: DonationStatus = DonationStatus.DISTRIBUTED) -> list[Donation]:
    statement = select(Donation).where(Donation.status == status.value).order_by(Donation.created_at.desc())
    return list(db.scalars(statement))
