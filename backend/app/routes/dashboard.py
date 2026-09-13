from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.donation import Donation, DonationStatus
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    ActivityItem,
    DonationSummaryItem,
    DonorDashboardResponse,
    ReceiverDashboardResponse,
)
from app.services.dashboard_service import (
    available_donation_count,
    count_donations,
    quantity_totals_by_unit,
    recent_donor_donations,
    recent_receiver_donations,
    status_counts_for_donations,
)
from app.services.donation_service import expire_available_donations
from app.utils.dependencies import require_roles

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/donor", response_model=DonorDashboardResponse)
def get_donor_dashboard(
    current_user: User = Depends(require_roles(UserRole.DONOR)),
    db: Session = Depends(get_db),
) -> DonorDashboardResponse:
    expire_available_donations(db)
    counts = status_counts_for_donations(db, Donation.donor_id == current_user.id)
    recent_donations = recent_donor_donations(db, current_user.id)

    return DonorDashboardResponse(
        total_donations=count_donations(db, Donation.donor_id == current_user.id),
        available_donations=counts.get(DonationStatus.AVAILABLE.value, 0),
        accepted_donations=counts.get(DonationStatus.ACCEPTED.value, 0),
        collected_donations=counts.get(DonationStatus.COLLECTED.value, 0),
        distributed_donations=counts.get(DonationStatus.DISTRIBUTED.value, 0),
        cancelled_donations=counts.get(DonationStatus.CANCELLED.value, 0),
        expired_donations=counts.get(DonationStatus.EXPIRED.value, 0),
        total_quantity_donated=quantity_totals_by_unit(db, Donation.donor_id == current_user.id),
        recent_donations=[DonationSummaryItem.model_validate(donation) for donation in recent_donations],
        recent_activity=build_donor_activity(recent_donations),
    )


@router.get("/receiver", response_model=ReceiverDashboardResponse)
def get_receiver_dashboard(
    current_user: User = Depends(require_roles(UserRole.NGO, UserRole.VOLUNTEER)),
    db: Session = Depends(get_db),
) -> ReceiverDashboardResponse:
    expire_available_donations(db)
    personal_condition = Donation.accepted_by_user_id == current_user.id
    counts = status_counts_for_donations(db, personal_condition)
    recent_donations = recent_receiver_donations(db, current_user.id)

    return ReceiverDashboardResponse(
        available_donations_count=available_donation_count(db),
        accepted_count=counts.get(DonationStatus.ACCEPTED.value, 0),
        collected_count=counts.get(DonationStatus.COLLECTED.value, 0),
        distributed_count=counts.get(DonationStatus.DISTRIBUTED.value, 0),
        total_rescued_quantity=quantity_totals_by_unit(
            db,
            personal_condition,
            Donation.status == DonationStatus.DISTRIBUTED.value,
        ),
        recent_accepted_donations=[
            DonationSummaryItem.model_validate(donation) for donation in recent_donations
        ],
        recent_activity=build_receiver_activity(recent_donations),
    )


def build_donor_activity(donations: list[Donation]) -> list[ActivityItem]:
    activities: list[ActivityItem] = []
    for donation in donations:
        activities.append(ActivityItem(message=f"Donation created: {donation.food_name}", happened_at=donation.created_at))
        if donation.accepted_at:
            activities.append(ActivityItem(message=f"Donation accepted: {donation.food_name}", happened_at=donation.accepted_at))
        if donation.collected_at:
            activities.append(ActivityItem(message=f"Donation collected: {donation.food_name}", happened_at=donation.collected_at))
        if donation.distributed_at:
            activities.append(ActivityItem(message=f"Donation distributed: {donation.food_name}", happened_at=donation.distributed_at))
    return sorted(activities, key=lambda activity: activity.happened_at, reverse=True)[:5]


def build_receiver_activity(donations: list[Donation]) -> list[ActivityItem]:
    activities: list[ActivityItem] = []
    for donation in donations:
        if donation.accepted_at:
            activities.append(ActivityItem(message=f"Donation accepted: {donation.food_name}", happened_at=donation.accepted_at))
        if donation.collected_at:
            activities.append(ActivityItem(message=f"Donation collected: {donation.food_name}", happened_at=donation.collected_at))
        if donation.distributed_at:
            activities.append(ActivityItem(message=f"Donation distributed: {donation.food_name}", happened_at=donation.distributed_at))
    return sorted(activities, key=lambda activity: activity.happened_at, reverse=True)[:5]
