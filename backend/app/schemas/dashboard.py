from datetime import datetime

from pydantic import BaseModel

from app.models.donation import DonationStatus, FoodType, QuantityUnit
from app.models.user import UserRole


class DonationSummaryItem(BaseModel):
    id: str
    food_name: str
    food_type: FoodType
    quantity: float
    quantity_unit: QuantityUnit
    status: DonationStatus
    created_at: datetime
    accepted_at: datetime | None = None
    collected_at: datetime | None = None
    distributed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ActivityItem(BaseModel):
    message: str
    happened_at: datetime


class DonorDashboardResponse(BaseModel):
    total_donations: int
    available_donations: int
    accepted_donations: int
    collected_donations: int
    distributed_donations: int
    cancelled_donations: int
    expired_donations: int
    total_quantity_donated: dict[str, float]
    recent_donations: list[DonationSummaryItem]
    recent_activity: list[ActivityItem]


class ReceiverDashboardResponse(BaseModel):
    available_donations_count: int
    accepted_count: int
    collected_count: int
    distributed_count: int
    total_rescued_quantity: dict[str, float]
    recent_accepted_donations: list[DonationSummaryItem]
    recent_activity: list[ActivityItem]


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_donors: int
    total_ngos: int
    total_volunteers: int
    total_admins: int
    total_donations: int
    available_donations: int
    accepted_donations: int
    collected_donations: int
    distributed_donations: int
    cancelled_donations: int
    expired_donations: int
    quantity_rescued_by_unit: dict[str, float]


class AdminUserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    role: UserRole
    organization_name: str | None
    location: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserDetailResponse(AdminUserResponse):
    donations_created: int
    donations_accepted: int
    donations_distributed: int


class AdminDonationResponse(BaseModel):
    id: str
    food_name: str
    food_type: FoodType
    quantity: float
    quantity_unit: QuantityUnit
    status: DonationStatus
    donor_id: str
    accepted_by_user_id: str | None
    created_at: datetime
    accepted_at: datetime | None
    collected_at: datetime | None
    distributed_at: datetime | None

    model_config = {"from_attributes": True}


class AdminDonationDetailResponse(AdminDonationResponse):
    description: str | None
    prepared_at: datetime
    available_until: datetime
    pickup_address: str
    latitude: float | None
    longitude: float | None
    image_url: str | None
    donor_name: str | None = None
    donor_email: str | None = None
    donor_phone: str | None = None
    donor_organization_name: str | None = None
    accepted_by_name: str | None = None
    accepted_by_email: str | None = None
    accepted_by_phone: str | None = None
    accepted_by_organization_name: str | None = None


class PaginatedUsersResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminUserResponse]


class PaginatedDonationsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminDonationResponse]
