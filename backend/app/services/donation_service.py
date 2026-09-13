from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.donation import Donation, DonationStatus, FoodType, QuantityUnit
from app.schemas.donation import DonationCreate, DonationUpdate, normalize_datetime
from app.services.notification_service import notify_donation_expired
from app.utils.location import haversine_distance_km


def create_donation(db: Session, donation_in: DonationCreate, donor_id: str) -> Donation:
    donation = Donation(
        donor_id=donor_id,
        food_name=donation_in.food_name,
        food_type=donation_in.food_type.value,
        quantity=donation_in.quantity,
        quantity_unit=donation_in.quantity_unit.value,
        description=donation_in.description,
        prepared_at=donation_in.prepared_at,
        available_until=donation_in.available_until,
        pickup_address=donation_in.pickup_address,
        latitude=donation_in.latitude,
        longitude=donation_in.longitude,
        image_url=donation_in.image_url,
        status=DonationStatus.AVAILABLE.value,
    )
    db.add(donation)
    db.commit()
    db.refresh(donation)
    return donation


def get_donation_by_id(db: Session, donation_id: str) -> Donation | None:
    donation = db.get(Donation, donation_id)
    if donation is not None:
        mark_expired_if_needed(db, donation)
    return donation


def list_my_donations(db: Session, donor_id: str, status_filter: DonationStatus | None = None) -> list[Donation]:
    expire_available_donations(db)
    statement = select(Donation).where(Donation.donor_id == donor_id).order_by(Donation.created_at.desc())
    if status_filter is not None:
        statement = statement.where(Donation.status == status_filter.value)
    return list(db.scalars(statement))


def list_available_donations(
    db: Session,
    food_type: FoodType | None = None,
    quantity_unit: QuantityUnit | None = None,
) -> list[Donation]:
    expire_available_donations(db)
    statement = select(Donation).where(Donation.status == DonationStatus.AVAILABLE.value)
    if food_type is not None:
        statement = statement.where(Donation.food_type == food_type.value)
    if quantity_unit is not None:
        statement = statement.where(Donation.quantity_unit == quantity_unit.value)
    statement = statement.order_by(Donation.created_at.desc())
    return list(db.scalars(statement))


def list_nearby_available_donations(
    db: Session,
    user_latitude: float,
    user_longitude: float,
    radius_km: float | None = None,
    food_type: FoodType | None = None,
    quantity_unit: QuantityUnit | None = None,
) -> list[tuple[Donation, float]]:
    expire_available_donations(db)
    statement = select(Donation).where(
        Donation.status == DonationStatus.AVAILABLE.value,
        Donation.latitude.is_not(None),
        Donation.longitude.is_not(None),
    )
    if food_type is not None:
        statement = statement.where(Donation.food_type == food_type.value)
    if quantity_unit is not None:
        statement = statement.where(Donation.quantity_unit == quantity_unit.value)

    nearby: list[tuple[Donation, float]] = []
    for donation in db.scalars(statement):
        distance_km = haversine_distance_km(
            user_latitude,
            user_longitude,
            donation.latitude,
            donation.longitude,
        )
        if radius_km is None or distance_km <= radius_km:
            nearby.append((donation, distance_km))

    return sorted(nearby, key=lambda item: item[1])


def update_donation(db: Session, donation: Donation, donation_in: DonationUpdate) -> Donation:
    update_data = donation_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(donation, field, value)

    if normalize_datetime(donation.prepared_at) >= normalize_datetime(donation.available_until):
        raise ValueError("prepared_at must be earlier than available_until")

    db.add(donation)
    db.commit()
    db.refresh(donation)
    return donation


def cancel_donation(db: Session, donation: Donation) -> Donation:
    donation.status = DonationStatus.CANCELLED.value
    db.add(donation)
    db.commit()
    db.refresh(donation)
    return donation


def accept_donation(db: Session, donation_id: str, accepted_by_user_id: str) -> Donation | None:
    return transition_donation_status(
        db=db,
        donation_id=donation_id,
        from_status=DonationStatus.AVAILABLE,
        to_status=DonationStatus.ACCEPTED,
        extra_conditions=[
            Donation.accepted_by_user_id.is_(None),
        ],
        update_values={
            "accepted_by_user_id": accepted_by_user_id,
            "accepted_at": datetime.now(timezone.utc),
        },
    )


def collect_donation(db: Session, donation_id: str, accepted_by_user_id: str) -> Donation | None:
    now = datetime.now(timezone.utc)
    return transition_donation_status(
        db=db,
        donation_id=donation_id,
        from_status=DonationStatus.ACCEPTED,
        to_status=DonationStatus.COLLECTED,
        accepted_by_user_id=accepted_by_user_id,
        update_values={"collected_at": now},
    )


def distribute_donation(db: Session, donation_id: str, accepted_by_user_id: str) -> Donation | None:
    now = datetime.now(timezone.utc)
    return transition_donation_status(
        db=db,
        donation_id=donation_id,
        from_status=DonationStatus.COLLECTED,
        to_status=DonationStatus.DISTRIBUTED,
        accepted_by_user_id=accepted_by_user_id,
        update_values={"distributed_at": now},
    )


def transition_donation_status(
    db: Session,
    donation_id: str,
    from_status: DonationStatus,
    to_status: DonationStatus,
    accepted_by_user_id: str | None = None,
    extra_conditions: list | None = None,
    update_values: dict | None = None,
) -> Donation | None:
    now = datetime.now(timezone.utc)
    conditions = [
        Donation.id == donation_id,
        Donation.status == from_status.value,
    ]
    if accepted_by_user_id is not None:
        conditions.append(Donation.accepted_by_user_id == accepted_by_user_id)
    if extra_conditions:
        conditions.extend(extra_conditions)

    values = {
        "status": to_status.value,
        "updated_at": now,
    }
    if update_values:
        values.update(update_values)

    statement = update(Donation).where(*conditions).values(**values)
    result = db.execute(statement.execution_options(synchronize_session=False))
    db.commit()
    if result.rowcount != 1:
        return None
    return get_donation_by_id(db, donation_id)


def list_accepted_by_user(
    db: Session,
    accepted_by_user_id: str,
    status_filter: DonationStatus | None = None,
) -> list[Donation]:
    expire_available_donations(db)
    statement = (
        select(Donation)
        .where(Donation.accepted_by_user_id == accepted_by_user_id)
        .order_by(Donation.accepted_at.desc())
    )
    if status_filter is not None:
        statement = statement.where(Donation.status == status_filter.value)
    return list(db.scalars(statement))


def expire_available_donations(db: Session) -> None:
    now = datetime.now(timezone.utc)
    statement = select(Donation).where(
        Donation.status == DonationStatus.AVAILABLE.value,
        Donation.available_until <= now,
    )
    expired_donations = list(db.scalars(statement))
    for donation in expired_donations:
        donation.status = DonationStatus.EXPIRED.value
        notify_donation_expired(db, donation, commit=False)
    if expired_donations:
        db.commit()


def mark_expired_if_needed(db: Session, donation: Donation) -> Donation:
    if donation.status != DonationStatus.AVAILABLE.value:
        return donation
    if normalize_datetime(donation.available_until) > datetime.now(timezone.utc):
        return donation

    donation.status = DonationStatus.EXPIRED.value
    notify_donation_expired(db, donation, commit=False)
    db.add(donation)
    db.commit()
    db.refresh(donation)
    return donation
