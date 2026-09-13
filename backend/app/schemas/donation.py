from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.donation import DonationStatus, FoodType, QuantityUnit


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def validate_future_available_until(value: datetime) -> datetime:
    value = normalize_datetime(value)
    if value <= datetime.now(timezone.utc):
        raise ValueError("available_until must be later than the current time")
    return value


def validate_reasonable_prepared_at(value: datetime) -> datetime:
    value = normalize_datetime(value)
    if value > datetime.now(timezone.utc) + timedelta(days=1):
        raise ValueError("prepared_at cannot be more than 1 day in the future")
    return value


class DonationBase(BaseModel):
    food_name: str = Field(min_length=1, max_length=120)
    food_type: FoodType
    quantity: float = Field(gt=0)
    quantity_unit: QuantityUnit
    description: str | None = Field(default=None, max_length=1000)
    prepared_at: datetime
    available_until: datetime
    pickup_address: str = Field(min_length=1, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    image_url: str | None = Field(default=None, max_length=500)

    @field_validator("food_name", "description", "pickup_address", "image_url")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value

    @field_validator("prepared_at")
    @classmethod
    def prepared_at_must_be_reasonable(cls, value: datetime) -> datetime:
        return validate_reasonable_prepared_at(value)

    @field_validator("available_until")
    @classmethod
    def available_until_must_be_future(cls, value: datetime) -> datetime:
        return validate_future_available_until(value)

    @model_validator(mode="after")
    def prepared_at_must_be_before_available_until(self):
        if self.prepared_at >= self.available_until:
            raise ValueError("prepared_at must be earlier than available_until")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Both latitude and longitude are required when saving pickup coordinates")
        return self


class DonationCreate(DonationBase):
    pass


class DonationUpdate(BaseModel):
    food_name: str | None = Field(default=None, min_length=1, max_length=120)
    food_type: FoodType | None = None
    quantity: float | None = Field(default=None, gt=0)
    quantity_unit: QuantityUnit | None = None
    description: str | None = Field(default=None, max_length=1000)
    prepared_at: datetime | None = None
    available_until: datetime | None = None
    pickup_address: str | None = Field(default=None, min_length=1, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    image_url: str | None = Field(default=None, max_length=500)

    @field_validator("food_name", "description", "pickup_address", "image_url")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value

    @field_validator("prepared_at")
    @classmethod
    def prepared_at_must_be_reasonable(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return validate_reasonable_prepared_at(value)

    @field_validator("available_until")
    @classmethod
    def available_until_must_be_future(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return validate_future_available_until(value)

    @model_validator(mode="after")
    def coordinates_must_be_complete(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Both latitude and longitude are required when saving pickup coordinates")
        return self


class DonationResponse(BaseModel):
    id: str
    donor_id: str
    food_name: str
    food_type: FoodType
    quantity: float
    quantity_unit: QuantityUnit
    description: str | None
    prepared_at: datetime
    available_until: datetime
    pickup_address: str
    latitude: float | None
    longitude: float | None
    image_url: str | None
    accepted_by_user_id: str | None
    accepted_at: datetime | None
    collected_at: datetime | None
    distributed_at: datetime | None
    status: DonationStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DonationListResponse(BaseModel):
    donations: list[DonationResponse]


class DonationDetailResponse(DonationResponse):
    donor_name: str | None = None
    donor_organization_name: str | None = None
    donor_phone: str | None = None
    accepted_by_name: str | None = None
    accepted_by_organization_name: str | None = None


class NearbyDonationResponse(BaseModel):
    id: str
    food_name: str
    food_type: FoodType
    quantity: float
    quantity_unit: QuantityUnit
    pickup_address: str
    latitude: float
    longitude: float
    available_until: datetime
    distance_km: float
    status: DonationStatus
