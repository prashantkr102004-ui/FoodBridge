from datetime import date

from pydantic import BaseModel


class MonthlyActivityItem(BaseModel):
    month: str
    created: int = 0
    distributed: int = 0


class ImpactDonationItem(BaseModel):
    id: str
    food_name: str
    quantity: float
    quantity_unit: str
    distributed_at: date | None = None


class DonorAnalyticsResponse(BaseModel):
    total_donations: int
    distributed_donations: int
    active_donations: int
    cancelled_donations: int
    expired_donations: int
    success_rate: float
    quantity_by_unit: dict[str, float]
    distributed_quantity_by_unit: dict[str, float]
    food_type_breakdown: dict[str, int]
    monthly_activity: list[MonthlyActivityItem]
    recent_impact: list[ImpactDonationItem]


class ReceiverAnalyticsResponse(BaseModel):
    total_accepted: int
    currently_accepted: int
    collected: int
    distributed: int
    completion_rate: float
    quantity_rescued_by_unit: dict[str, float]
    food_type_breakdown: dict[str, int]
    monthly_activity: list[MonthlyActivityItem]
    recent_impact: list[ImpactDonationItem]


class AdminAnalyticsResponse(BaseModel):
    total_users: int
    total_donations: int
    total_distributed: int
    total_cancelled: int
    total_expired: int
    distribution_success_rate: float
    users_by_role: dict[str, int]
    donations_by_status: dict[str, int]
    quantity_distributed_by_unit: dict[str, float]
    food_type_breakdown: dict[str, int]
    monthly_donation_activity: list[MonthlyActivityItem]
