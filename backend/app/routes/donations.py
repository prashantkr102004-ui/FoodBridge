from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.donation import Donation, DonationStatus, FoodType, QuantityUnit
from app.models.user import User, UserRole
from app.schemas.donation import DonationCreate, DonationDetailResponse, DonationResponse, DonationUpdate, NearbyDonationResponse
from app.services.donation_service import (
    accept_donation,
    cancel_donation,
    collect_donation,
    create_donation,
    distribute_donation,
    get_donation_by_id,
    list_available_donations,
    list_accepted_by_user,
    list_my_donations,
    list_nearby_available_donations,
    update_donation,
)
from app.services.notification_service import (
    notify_donation_accepted,
    notify_donation_collected,
    notify_donation_distributed,
)
from app.utils.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/donations", tags=["Donations"])


@router.post("", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
def create_food_donation(
    donation_in: DonationCreate,
    current_user: User = Depends(require_roles(UserRole.DONOR)),
    db: Session = Depends(get_db),
) -> Donation:
    return create_donation(db, donation_in, donor_id=current_user.id)


@router.get("/my", response_model=list[DonationResponse])
def get_my_donations(
    status: DonationStatus | None = None,
    current_user: User = Depends(require_roles(UserRole.DONOR)),
    db: Session = Depends(get_db),
) -> list[Donation]:
    return list_my_donations(db, donor_id=current_user.id, status_filter=status)


@router.get("/accepted/my", response_model=list[DonationDetailResponse])
def get_my_accepted_donations(
    status: DonationStatus | None = None,
    current_user: User = Depends(require_roles(UserRole.NGO, UserRole.VOLUNTEER)),
    db: Session = Depends(get_db),
) -> list[DonationDetailResponse]:
    donations = list_accepted_by_user(db, accepted_by_user_id=current_user.id, status_filter=status)
    return [build_donation_detail_response(donation, current_user) for donation in donations]


@router.get("", response_model=list[DonationResponse])
def get_available_donations(
    food_type: FoodType | None = None,
    quantity_unit: QuantityUnit | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Donation]:
    return list_available_donations(db, food_type=food_type, quantity_unit=quantity_unit)


@router.get("/nearby", response_model=list[NearbyDonationResponse])
def get_nearby_available_donations(
    radius_km: float | None = None,
    food_type: FoodType | None = None,
    quantity_unit: QuantityUnit | None = None,
    current_user: User = Depends(require_roles(UserRole.NGO, UserRole.VOLUNTEER)),
    db: Session = Depends(get_db),
) -> list[NearbyDonationResponse]:
    if current_user.latitude is None or current_user.longitude is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set your location before using nearby donations.",
        )
    if radius_km is not None and (radius_km <= 0 or radius_km > 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="radius_km must be between 0 and 100",
        )

    nearby = list_nearby_available_donations(
        db=db,
        user_latitude=current_user.latitude,
        user_longitude=current_user.longitude,
        radius_km=radius_km,
        food_type=food_type,
        quantity_unit=quantity_unit,
    )
    return [
        NearbyDonationResponse(
            id=donation.id,
            food_name=donation.food_name,
            food_type=donation.food_type,
            quantity=donation.quantity,
            quantity_unit=donation.quantity_unit,
            pickup_address=donation.pickup_address,
            latitude=donation.latitude,
            longitude=donation.longitude,
            available_until=donation.available_until,
            distance_km=round(distance_km, 2),
            status=donation.status,
        )
        for donation, distance_km in nearby
    ]


@router.get("/{donation_id}", response_model=DonationDetailResponse)
def get_donation(
    donation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DonationDetailResponse:
    donation = get_donation_by_id(db, donation_id)
    if donation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
    return build_donation_detail_response(donation, current_user)


@router.patch("/{donation_id}", response_model=DonationResponse)
def update_food_donation(
    donation_id: str,
    donation_in: DonationUpdate,
    current_user: User = Depends(require_roles(UserRole.DONOR)),
    db: Session = Depends(get_db),
) -> Donation:
    donation = get_owned_donation_or_404(db, donation_id, current_user)
    ensure_available_for_change(donation)

    try:
        return update_donation(db, donation, donation_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{donation_id}/cancel", response_model=DonationResponse)
def cancel_food_donation(
    donation_id: str,
    current_user: User = Depends(require_roles(UserRole.DONOR)),
    db: Session = Depends(get_db),
) -> Donation:
    donation = get_owned_donation_or_404(db, donation_id, current_user)
    ensure_available_for_change(donation)
    return cancel_donation(db, donation)


@router.post("/{donation_id}/accept", response_model=DonationDetailResponse)
def accept_food_donation(
    donation_id: str,
    current_user: User = Depends(require_roles(UserRole.NGO, UserRole.VOLUNTEER)),
    db: Session = Depends(get_db),
) -> DonationDetailResponse:
    donation = get_donation_by_id(db, donation_id)
    if donation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
    if donation.status != DonationStatus.AVAILABLE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only AVAILABLE donations can be accepted",
        )

    accepted_donation = accept_donation(db, donation_id, accepted_by_user_id=current_user.id)
    if accepted_donation is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Donation is no longer available for acceptance",
        )
    notify_donation_accepted(db, accepted_donation, current_user)
    return build_donation_detail_response(accepted_donation, current_user)


@router.post("/{donation_id}/collect", response_model=DonationDetailResponse)
def collect_food_donation(
    donation_id: str,
    current_user: User = Depends(require_roles(UserRole.NGO, UserRole.VOLUNTEER)),
    db: Session = Depends(get_db),
) -> DonationDetailResponse:
    donation = get_donation_by_id(db, donation_id)
    if donation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
    if donation.status != DonationStatus.ACCEPTED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Donation must be ACCEPTED before it can be marked collected.",
        )
    ensure_current_user_accepted_donation(donation, current_user)

    collected_donation = collect_donation(db, donation_id, accepted_by_user_id=current_user.id)
    if collected_donation is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Donation could not be marked collected because its state changed.",
        )
    notify_donation_collected(db, collected_donation, current_user)
    return build_donation_detail_response(collected_donation, current_user)


@router.post("/{donation_id}/distribute", response_model=DonationDetailResponse)
def distribute_food_donation(
    donation_id: str,
    current_user: User = Depends(require_roles(UserRole.NGO, UserRole.VOLUNTEER)),
    db: Session = Depends(get_db),
) -> DonationDetailResponse:
    donation = get_donation_by_id(db, donation_id)
    if donation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
    if donation.status != DonationStatus.COLLECTED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Donation must be COLLECTED before it can be marked distributed.",
        )
    ensure_current_user_accepted_donation(donation, current_user)

    distributed_donation = distribute_donation(db, donation_id, accepted_by_user_id=current_user.id)
    if distributed_donation is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Donation could not be marked distributed because its state changed.",
        )
    notify_donation_distributed(db, distributed_donation, current_user)
    return build_donation_detail_response(distributed_donation, current_user)


def get_owned_donation_or_404(db: Session, donation_id: str, current_user: User) -> Donation:
    donation = get_donation_by_id(db, donation_id)
    if donation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
    if donation.donor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own donations",
        )
    return donation


def ensure_available_for_change(donation: Donation) -> None:
    if donation.status != DonationStatus.AVAILABLE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only AVAILABLE donations can be changed in Phase 2",
        )


def ensure_current_user_accepted_donation(donation: Donation, current_user: User) -> None:
    if donation.accepted_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the NGO or volunteer who accepted this donation can update its pickup status.",
        )


def build_donation_detail_response(donation: Donation, current_user: User) -> DonationDetailResponse:
    response = DonationDetailResponse.model_validate(donation)

    is_donor_owner = current_user.id == donation.donor_id
    is_accepting_user = current_user.id == donation.accepted_by_user_id

    if is_donor_owner and donation.accepted_by_user is not None:
        response.accepted_by_name = donation.accepted_by_user.name
        response.accepted_by_organization_name = donation.accepted_by_user.organization_name

    if is_accepting_user and donation.donor is not None:
        response.donor_name = donation.donor.name
        response.donor_organization_name = donation.donor.organization_name
        response.donor_phone = donation.donor.phone

    return response
