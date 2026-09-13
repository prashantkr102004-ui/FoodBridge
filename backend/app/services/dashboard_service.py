from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.donation import Donation, DonationStatus, FoodType
from app.models.user import User, UserRole


def status_counts_for_donations(db: Session, *conditions) -> dict[str, int]:
    statement = select(Donation.status, func.count(Donation.id)).where(*conditions).group_by(Donation.status)
    return {status: count for status, count in db.execute(statement).all()}


def user_counts_by_role(db: Session) -> dict[str, int]:
    statement = select(User.role, func.count(User.id)).group_by(User.role)
    return {role: count for role, count in db.execute(statement).all()}


def count_donations(db: Session, *conditions) -> int:
    statement = select(func.count(Donation.id)).where(*conditions)
    return db.scalar(statement) or 0


def count_users(db: Session, *conditions) -> int:
    statement = select(func.count(User.id)).where(*conditions)
    return db.scalar(statement) or 0


def quantity_totals_by_unit(db: Session, *conditions) -> dict[str, float]:
    statement = (
        select(Donation.quantity_unit, func.sum(Donation.quantity))
        .where(*conditions)
        .group_by(Donation.quantity_unit)
    )
    return {unit: float(total or 0) for unit, total in db.execute(statement).all()}


def recent_donor_donations(db: Session, donor_id: str, limit: int = 5) -> list[Donation]:
    statement = (
        select(Donation)
        .where(Donation.donor_id == donor_id)
        .order_by(Donation.updated_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement))


def recent_receiver_donations(db: Session, accepted_by_user_id: str, limit: int = 5) -> list[Donation]:
    statement = (
        select(Donation)
        .where(Donation.accepted_by_user_id == accepted_by_user_id)
        .order_by(Donation.updated_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement))


def available_donation_count(db: Session) -> int:
    return count_donations(db, Donation.status == DonationStatus.AVAILABLE.value)


def list_admin_users(
    db: Session,
    page: int,
    page_size: int,
    role: UserRole | None = None,
    search: str | None = None,
) -> tuple[int, list[User]]:
    conditions = []
    if role is not None:
        conditions.append(User.role == role.value)
    if search:
        like_pattern = f"%{search.strip()}%"
        conditions.append(
            or_(
                User.name.ilike(like_pattern),
                User.email.ilike(like_pattern),
                User.organization_name.ilike(like_pattern),
            )
        )

    total = count_users(db, *conditions)
    statement = (
        select(User)
        .where(*conditions)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return total, list(db.scalars(statement))


def get_admin_user_detail_counts(db: Session, user_id: str) -> dict[str, int]:
    return {
        "donations_created": count_donations(db, Donation.donor_id == user_id),
        "donations_accepted": count_donations(db, Donation.accepted_by_user_id == user_id),
        "donations_distributed": count_donations(
            db,
            Donation.accepted_by_user_id == user_id,
            Donation.status == DonationStatus.DISTRIBUTED.value,
        ),
    }


def list_admin_donations(
    db: Session,
    page: int,
    page_size: int,
    status_filter: DonationStatus | None = None,
    food_type: FoodType | None = None,
    donor_id: str | None = None,
    accepted_by_user_id: str | None = None,
) -> tuple[int, list[Donation]]:
    conditions = []
    if status_filter is not None:
        conditions.append(Donation.status == status_filter.value)
    if food_type is not None:
        conditions.append(Donation.food_type == food_type.value)
    if donor_id:
        conditions.append(Donation.donor_id == donor_id)
    if accepted_by_user_id:
        conditions.append(Donation.accepted_by_user_id == accepted_by_user_id)

    total = count_donations(db, *conditions)
    statement = (
        select(Donation)
        .where(*conditions)
        .order_by(Donation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return total, list(db.scalars(statement))


def get_admin_donation(db: Session, donation_id: str) -> Donation | None:
    statement = (
        select(Donation)
        .options(joinedload(Donation.donor), joinedload(Donation.accepted_by_user))
        .where(Donation.id == donation_id)
    )
    return db.scalar(statement)
