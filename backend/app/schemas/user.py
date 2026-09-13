from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.user import UserRole


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    organization_name: str | None = Field(default=None, max_length=150)
    receiver_type: str | None = Field(default=None, max_length=20)
    receiver_focus: str | None = Field(default=None, max_length=150)
    profile_image_url: str | None = Field(default=None, max_length=255)
    location: str = Field(min_length=2, max_length=150)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("name", "phone", "organization_name", "receiver_type", "receiver_focus", "profile_image_url", "location")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value

    @model_validator(mode="after")
    def coordinates_must_be_complete(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Both latitude and longitude are required when saving coordinates")
        if self.receiver_type is not None and self.receiver_type not in {"HUMAN", "ANIMAL"}:
            raise ValueError("Receiver type must be HUMAN or ANIMAL")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: str
    role: UserRole
    organization_name: str | None
    receiver_type: str | None
    receiver_focus: str | None
    profile_image_url: str | None
    location: str
    latitude: float | None
    longitude: float | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLocationUpdate(BaseModel):
    location: str | None = Field(default=None, min_length=2, max_length=150)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("location")
    @classmethod
    def strip_location(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value

    @model_validator(mode="after")
    def coordinates_must_be_complete(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Both latitude and longitude are required when saving coordinates")
        return self
