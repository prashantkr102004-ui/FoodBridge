from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.donation import DonationStatus, FoodType
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    AdminDashboardResponse,
    AdminDonationDetailResponse,
    AdminDonationResponse,
    AdminUserDetailResponse,
    AdminUserResponse,
    PaginatedDonationsResponse,
    PaginatedUsersResponse,
)
from app.services.dashboard_service import (
    count_donations,
    count_users,
    get_admin_donation,
    get_admin_user_detail_counts,
    list_admin_donations,
    list_admin_users,
    quantity_totals_by_unit,
    status_counts_for_donations,
    user_counts_by_role,
)
from app.services.donation_service import get_donation_by_id
from app.services.user_service import get_user_by_id
from app.models.donation import Donation
from app.utils.dependencies import require_roles

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> AdminDashboardResponse:
    role_counts = user_counts_by_role(db)
    donation_counts = status_counts_for_donations(db)

    return AdminDashboardResponse(
        total_users=count_users(db),
        total_donors=role_counts.get(UserRole.DONOR.value, 0),
        total_ngos=role_counts.get(UserRole.NGO.value, 0),
        total_volunteers=role_counts.get(UserRole.VOLUNTEER.value, 0),
        total_admins=role_counts.get(UserRole.ADMIN.value, 0),
        total_donations=count_donations(db),
        available_donations=donation_counts.get(DonationStatus.AVAILABLE.value, 0),
        accepted_donations=donation_counts.get(DonationStatus.ACCEPTED.value, 0),
        collected_donations=donation_counts.get(DonationStatus.COLLECTED.value, 0),
        distributed_donations=donation_counts.get(DonationStatus.DISTRIBUTED.value, 0),
        cancelled_donations=donation_counts.get(DonationStatus.CANCELLED.value, 0),
        expired_donations=donation_counts.get(DonationStatus.EXPIRED.value, 0),
        quantity_rescued_by_unit=quantity_totals_by_unit(
            db,
            Donation.status == DonationStatus.DISTRIBUTED.value,
        ),
    )


@router.get("/users", response_model=PaginatedUsersResponse)
def get_admin_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: UserRole | None = None,
    search: str | None = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> PaginatedUsersResponse:
    total, users = list_admin_users(db, page=page, page_size=page_size, role=role, search=search)
    return PaginatedUsersResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[AdminUserResponse.model_validate(user) for user in users],
    )


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
def get_admin_user_detail(
    user_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> AdminUserDetailResponse:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return AdminUserDetailResponse(
        **AdminUserResponse.model_validate(user).model_dump(),
        **get_admin_user_detail_counts(db, user_id),
    )


@router.post("/users/{user_id}/deactivate", response_model=AdminUserResponse)
def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> User:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot deactivate their own account",
        )
    user.is_active = False
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/activate", response_model=AdminUserResponse)
def activate_user(
    user_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> User:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/donations", response_model=PaginatedDonationsResponse)
def get_admin_donations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: DonationStatus | None = None,
    food_type: FoodType | None = None,
    donor_id: str | None = None,
    accepted_by_user_id: str | None = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> PaginatedDonationsResponse:
    total, donations = list_admin_donations(
        db,
        page=page,
        page_size=page_size,
        status_filter=status,
        food_type=food_type,
        donor_id=donor_id,
        accepted_by_user_id=accepted_by_user_id,
    )
    return PaginatedDonationsResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[AdminDonationResponse.model_validate(donation) for donation in donations],
    )


@router.get("/donations/{donation_id}", response_model=AdminDonationDetailResponse)
def get_admin_donation_detail(
    donation_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> AdminDonationDetailResponse:
    donation = get_admin_donation(db, donation_id)
    if donation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
    return build_admin_donation_detail(donation)


def build_admin_donation_detail(donation) -> AdminDonationDetailResponse:
    data = AdminDonationDetailResponse.model_validate(donation)
    if donation.donor is not None:
        data.donor_name = donation.donor.name
        data.donor_email = donation.donor.email
        data.donor_phone = donation.donor.phone
        data.donor_organization_name = donation.donor.organization_name
    if donation.accepted_by_user is not None:
        data.accepted_by_name = donation.accepted_by_user.name
        data.accepted_by_email = donation.accepted_by_user.email
        data.accepted_by_phone = donation.accepted_by_user.phone
        data.accepted_by_organization_name = donation.accepted_by_user.organization_name
    return data
