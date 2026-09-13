from datetime import datetime

from pydantic import BaseModel

from app.models.donation import DonationStatus, FoodType, QuantityUnit


class ScoreBreakdown(BaseModel):
    distance: int
    urgency: int
    quantity: int
    preference: int


class DonationRecommendationResponse(BaseModel):
    id: str
    food_name: str
    food_type: FoodType
    quantity: float
    quantity_unit: QuantityUnit
    description: str | None
    pickup_address: str
    latitude: float
    longitude: float
    available_until: datetime
    status: DonationStatus
    distance_km: float
    match_score: int
    score_breakdown: ScoreBreakdown
    reasons: list[str]
