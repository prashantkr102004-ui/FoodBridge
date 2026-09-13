import csv
from datetime import date
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.donation import DonationStatus
from app.models.user import User, UserRole
from app.schemas.analytics import AdminAnalyticsResponse, DonorAnalyticsResponse, ReceiverAnalyticsResponse
from app.services.analytics_service import (
    export_impact_rows,
    get_admin_analytics,
    get_donor_analytics,
    get_receiver_analytics,
)
from app.services.donation_service import expire_available_donations
from app.utils.dependencies import require_roles

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def csv_safe(value) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


@router.get("/donor", response_model=DonorAnalyticsResponse)
def get_donor_impact_analytics(
    current_user: User = Depends(require_roles(UserRole.DONOR)),
    db: Session = Depends(get_db),
) -> DonorAnalyticsResponse:
    expire_available_donations(db)
    return get_donor_analytics(db, current_user.id)


@router.get("/receiver", response_model=ReceiverAnalyticsResponse)
def get_receiver_impact_analytics(
    current_user: User = Depends(require_roles(UserRole.NGO, UserRole.VOLUNTEER)),
    db: Session = Depends(get_db),
) -> ReceiverAnalyticsResponse:
    expire_available_donations(db)
    return get_receiver_analytics(db, current_user.id)


@router.get("/admin", response_model=AdminAnalyticsResponse)
def get_admin_platform_analytics(
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> AdminAnalyticsResponse:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before or equal to end_date")
    expire_available_donations(db)
    return get_admin_analytics(db, start_date=start_date, end_date=end_date)


@router.get("/admin/export.csv")
def export_admin_impact_csv(
    status_filter: DonationStatus = Query(default=DonationStatus.DISTRIBUTED, alias="status"),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> Response:
    expire_available_donations(db)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Donation ID",
            "Food Name",
            "Food Type",
            "Quantity",
            "Quantity Unit",
            "Status",
            "Created At",
            "Accepted At",
            "Collected At",
            "Distributed At",
        ]
    )
    for donation in export_impact_rows(db, status=status_filter):
        writer.writerow(
            [
                csv_safe(donation.id),
                csv_safe(donation.food_name),
                csv_safe(donation.food_type),
                csv_safe(donation.quantity),
                csv_safe(donation.quantity_unit),
                csv_safe(donation.status),
                csv_safe(donation.created_at.isoformat() if donation.created_at else ""),
                csv_safe(donation.accepted_at.isoformat() if donation.accepted_at else ""),
                csv_safe(donation.collected_at.isoformat() if donation.collected_at else ""),
                csv_safe(donation.distributed_at.isoformat() if donation.distributed_at else ""),
            ]
        )

    headers = {"Content-Disposition": 'attachment; filename="foodbridge-impact-report.csv"'}
    return Response(content=output.getvalue(), media_type="text/csv", headers=headers)
