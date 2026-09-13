from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.donation import Donation, DonationStatus, FoodType, QuantityUnit
from app.models.user import User
from app.schemas.donation import normalize_datetime
from app.schemas.recommendation import DonationRecommendationResponse, ScoreBreakdown
from app.services.donation_service import expire_available_donations
from app.utils.location import haversine_distance_km


DISTANCE_WEIGHT = 0.40
URGENCY_WEIGHT = 0.30
QUANTITY_WEIGHT = 0.15
PREFERENCE_WEIGHT = 0.15
DEFAULT_RADIUS_KM = 20.0
MAX_RADIUS_KM = 100.0
DEFAULT_LIMIT = 10
MAX_LIMIT = 50
MIN_HISTORY_ITEMS = 3

QUANTITY_TARGETS = {
    QuantityUnit.MEALS.value: 50,
    QuantityUnit.PACKETS.value: 50,
    QuantityUnit.KG.value: 25,
    QuantityUnit.OTHER.value: 20,
}


@dataclass(frozen=True)
class FoodPreferenceProfile:
    total_history: int
    counts_by_food_type: dict[str, int]


def calculate_distance_score(distance_km: float, radius_km: float) -> int:
    if distance_km >= radius_km:
        return 0
    return round(max(0, min(100, 100 * (1 - distance_km / radius_km))))


def calculate_urgency_score(available_until: datetime, now: datetime | None = None) -> int:
    current_time = now or datetime.now(timezone.utc)
    hours_remaining = (normalize_datetime(available_until) - current_time).total_seconds() / 3600
    if hours_remaining <= 0:
        return 0
    if hours_remaining <= 1:
        return 100
    if hours_remaining <= 2:
        return 85
    if hours_remaining <= 4:
        return 70
    if hours_remaining <= 8:
        return 50
    if hours_remaining <= 24:
        return 30
    return 15


def calculate_quantity_score(quantity: float, quantity_unit: str) -> int:
    target = QUANTITY_TARGETS.get(quantity_unit, QUANTITY_TARGETS[QuantityUnit.OTHER.value])
    return round(max(10, min(100, (quantity / target) * 100)))


def build_food_preference_profile(db: Session, user_id: str) -> FoodPreferenceProfile:
    statement = select(Donation.food_type).where(
        Donation.accepted_by_user_id == user_id,
        Donation.status.in_(
            [
                DonationStatus.ACCEPTED.value,
                DonationStatus.COLLECTED.value,
                DonationStatus.DISTRIBUTED.value,
            ]
        ),
    )
    counts: dict[str, int] = {}
    for food_type in db.scalars(statement):
        counts[food_type] = counts.get(food_type, 0) + 1
    return FoodPreferenceProfile(total_history=sum(counts.values()), counts_by_food_type=counts)


def calculate_preference_score(food_type: str, profile: FoodPreferenceProfile) -> int:
    if profile.total_history < MIN_HISTORY_ITEMS:
        return 70
    food_type_count = profile.counts_by_food_type.get(food_type, 0)
    return round(50 + 50 * (food_type_count / profile.total_history))


def calculate_match_score(
    distance_score: int,
    urgency_score: int,
    quantity_score: int,
    preference_score: int,
) -> int:
    weighted_score = (
        distance_score * DISTANCE_WEIGHT
        + urgency_score * URGENCY_WEIGHT
        + quantity_score * QUANTITY_WEIGHT
        + preference_score * PREFERENCE_WEIGHT
    )
    return round(max(0, min(100, weighted_score)))


def build_recommendation_reasons(
    donation: Donation,
    distance_km: float,
    urgency_score: int,
    quantity_score: int,
    preference_score: int,
    profile: FoodPreferenceProfile,
    now: datetime,
) -> list[str]:
    reasons: list[str] = []

    if distance_km <= 2:
        reasons.append(f"Only {distance_km:.1f} km away")
    elif distance_km <= 5:
        reasons.append(f"Nearby at {distance_km:.1f} km away")

    minutes_remaining = round((normalize_datetime(donation.available_until) - now).total_seconds() / 60)
    if urgency_score >= 100:
        reasons.append("Expires within 60 minutes")
    elif urgency_score >= 85:
        reasons.append("Expires within 2 hours")
    elif urgency_score >= 70:
        reasons.append("Expires within 4 hours")

    if quantity_score >= 80:
        reasons.append("Large available quantity")
    elif quantity_score >= 50:
        reasons.append("Suitable quantity for pickup")

    if profile.total_history >= MIN_HISTORY_ITEMS and preference_score >= 75:
        reasons.append("Matches your commonly accepted food type")

    if not reasons:
        reasons.append(f"Available for about {max(1, minutes_remaining // 60)} hours")

    return reasons[:4]


def get_donation_recommendations(
    db: Session,
    receiver: User,
    radius_km: float = DEFAULT_RADIUS_KM,
    food_type: FoodType | None = None,
    quantity_unit: QuantityUnit | None = None,
    limit: int = DEFAULT_LIMIT,
) -> list[DonationRecommendationResponse]:
    expire_available_donations(db)
    now = datetime.now(timezone.utc)
    profile = build_food_preference_profile(db, receiver.id)

    statement = select(Donation).where(
        Donation.status == DonationStatus.AVAILABLE.value,
        Donation.latitude.is_not(None),
        Donation.longitude.is_not(None),
        Donation.available_until > now,
    )
    if food_type is not None:
        statement = statement.where(Donation.food_type == food_type.value)
    if quantity_unit is not None:
        statement = statement.where(Donation.quantity_unit == quantity_unit.value)

    recommendations: list[DonationRecommendationResponse] = []
    for donation in db.scalars(statement):
        distance_km = haversine_distance_km(
            receiver.latitude,
            receiver.longitude,
            donation.latitude,
            donation.longitude,
        )
        if distance_km > radius_km:
            continue

        distance_score = calculate_distance_score(distance_km, radius_km)
        urgency_score = calculate_urgency_score(donation.available_until, now)
        quantity_score = calculate_quantity_score(donation.quantity, donation.quantity_unit)
        preference_score = calculate_preference_score(donation.food_type, profile)
        match_score = calculate_match_score(distance_score, urgency_score, quantity_score, preference_score)

        recommendations.append(
            DonationRecommendationResponse(
                id=donation.id,
                food_name=donation.food_name,
                food_type=donation.food_type,
                quantity=donation.quantity,
                quantity_unit=donation.quantity_unit,
                description=donation.description,
                pickup_address=donation.pickup_address,
                latitude=donation.latitude,
                longitude=donation.longitude,
                available_until=donation.available_until,
                status=donation.status,
                distance_km=round(distance_km, 2),
                match_score=match_score,
                score_breakdown=ScoreBreakdown(
                    distance=distance_score,
                    urgency=urgency_score,
                    quantity=quantity_score,
                    preference=preference_score,
                ),
                reasons=build_recommendation_reasons(
                    donation=donation,
                    distance_km=distance_km,
                    urgency_score=urgency_score,
                    quantity_score=quantity_score,
                    preference_score=preference_score,
                    profile=profile,
                    now=now,
                ),
            )
        )

    return sorted(recommendations, key=lambda item: item.match_score, reverse=True)[:limit]
