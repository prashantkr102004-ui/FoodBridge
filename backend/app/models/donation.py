import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User, utc_now


class FoodType(str, Enum):
    VEGETARIAN = "VEGETARIAN"
    NON_VEGETARIAN = "NON_VEGETARIAN"
    VEGAN = "VEGAN"
    OTHER = "OTHER"


class QuantityUnit(str, Enum):
    MEALS = "MEALS"
    PACKETS = "PACKETS"
    KG = "KG"
    OTHER = "OTHER"


class DonationStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ACCEPTED = "ACCEPTED"
    COLLECTED = "COLLECTED"
    DISTRIBUTED = "DISTRIBUTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class Donation(Base):
    __tablename__ = "donations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    donor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    food_name: Mapped[str] = mapped_column(String(120), nullable=False)
    food_type: Mapped[str] = mapped_column(String(30), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    quantity_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prepared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    available_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pickup_address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    accepted_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    distributed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=DonationStatus.AVAILABLE.value,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    donor: Mapped[User] = relationship(foreign_keys=[donor_id])
    accepted_by_user: Mapped[Optional[User]] = relationship(foreign_keys=[accepted_by_user_id])
