from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.donation import FoodType, QuantityUnit
from app.models.user import User, UserRole
from app.schemas.recommendation import DonationRecommendationResponse
from app.services.recommendation_service import (
    DEFAULT_LIMIT,
    DEFAULT_RADIUS_KM,
    MAX_LIMIT,
    MAX_RADIUS_KM,
    get_donation_recommendations,
)
from app.utils.dependencies import require_roles

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/donations", response_model=list[DonationRecommendationResponse])
def get_recommended_donations(
    radius_km: float = DEFAULT_RADIUS_KM,
    food_type: FoodType | None = None,
    quantity_unit: QuantityUnit | None = None,
    limit: int = DEFAULT_LIMIT,
    current_user: User = Depends(require_roles(UserRole.NGO, UserRole.VOLUNTEER)),
    db: Session = Depends(get_db),
) -> list[DonationRecommendationResponse]:
    if current_user.latitude is None or current_user.longitude is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set your location before using smart recommendations.",
        )
    if radius_km <= 0 or radius_km > MAX_RADIUS_KM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"radius_km must be between 0 and {int(MAX_RADIUS_KM)}",
        )
    if limit <= 0 or limit > MAX_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"limit must be between 1 and {MAX_LIMIT}",
        )

    return get_donation_recommendations(
        db=db,
        receiver=current_user,
        radius_km=radius_km,
        food_type=food_type,
        quantity_unit=quantity_unit,
        limit=limit,
    )
