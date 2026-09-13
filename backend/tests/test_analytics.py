from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.donation import Donation, DonationStatus
from app.models.user import User
from tests.test_donations import create_test_admin


def registration_payload(email: str, role: str) -> dict[str, object]:
    return {
        "name": f"{role.title()} User",
        "email": email,
        "phone": "9876543210",
        "password": "strongpass123",
        "role": role,
        "organization_name": f"{role.title()} Organization",
        "location": "Pune",
        "latitude": 18.5204,
        "longitude": 73.8567,
    }


def register_and_login(client: TestClient, email: str, role: str) -> str:
    if role == "ADMIN":
        create_test_admin(email)
    else:
        client.post("/auth/register", json=registration_payload(email, role))
    response = client.post("/auth/login", json={"email": email, "password": "strongpass123"})
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def donation_payload(food_name: str, quantity: float = 10, quantity_unit: str = "MEALS", food_type: str = "VEGETARIAN") -> dict[str, object]:
    now = datetime.now(timezone.utc)
    return {
        "food_name": food_name,
        "food_type": food_type,
        "quantity": quantity,
        "quantity_unit": quantity_unit,
        "description": "Fresh food",
        "prepared_at": now.isoformat(),
        "available_until": (now + timedelta(hours=5)).isoformat(),
        "pickup_address": "College Canteen, Pune",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "image_url": None,
    }


def create_donation(
    client: TestClient,
    donor_token: str,
    food_name: str,
    quantity: float = 10,
    quantity_unit: str = "MEALS",
    food_type: str = "VEGETARIAN",
) -> dict:
    response = client.post(
        "/donations",
        json=donation_payload(food_name, quantity, quantity_unit, food_type),
        headers=auth_header(donor_token),
    )
    assert response.status_code == 201
    return response.json()


def get_user_id(db: Session, email: str) -> str:
    return db.query(User).filter(User.email == email).one().id


def set_donation_state(
    db: Session,
    donation_id: str,
    status: DonationStatus,
    accepted_by_user_id: str | None = None,
    created_at: datetime | None = None,
) -> None:
    donation = db.get(Donation, donation_id)
    donation.status = status.value
    donation.accepted_by_user_id = accepted_by_user_id
    if created_at is not None:
        donation.created_at = created_at
    if status in {DonationStatus.ACCEPTED, DonationStatus.COLLECTED, DonationStatus.DISTRIBUTED}:
        donation.accepted_at = created_at or datetime.now(timezone.utc)
    if status in {DonationStatus.COLLECTED, DonationStatus.DISTRIBUTED}:
        donation.collected_at = created_at or datetime.now(timezone.utc)
    if status == DonationStatus.DISTRIBUTED:
        donation.distributed_at = created_at or datetime.now(timezone.utc)
    db.add(donation)
    db.commit()


def test_donor_analytics_requires_donor(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")

    assert client.get("/analytics/donor", headers=auth_header(donor_token)).status_code == 200
    assert client.get("/analytics/donor", headers=auth_header(ngo_token)).status_code == 403
    assert client.get("/analytics/donor").status_code == 401


def test_donor_analytics_are_scoped_and_calculated(client: TestClient, db_session: Session) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    other_token = register_and_login(client, "other@example.com", "DONOR")
    distributed_id = create_donation(client, donor_token, "Meals", quantity=20, quantity_unit="MEALS")["id"]
    kg_id = create_donation(client, donor_token, "Rice", quantity=5, quantity_unit="KG", food_type="VEGAN")["id"]
    cancelled_id = create_donation(client, donor_token, "Cancelled", quantity=2, quantity_unit="PACKETS")["id"]
    create_donation(client, donor_token, "Active", quantity=4, quantity_unit="MEALS")
    other_id = create_donation(client, other_token, "Other Donor", quantity=100, quantity_unit="MEALS")["id"]
    set_donation_state(db_session, distributed_id, DonationStatus.DISTRIBUTED)
    set_donation_state(db_session, kg_id, DonationStatus.DISTRIBUTED)
    set_donation_state(db_session, cancelled_id, DonationStatus.CANCELLED)
    set_donation_state(db_session, other_id, DonationStatus.DISTRIBUTED)

    response = client.get("/analytics/donor", headers=auth_header(donor_token))
    data = response.json()

    assert response.status_code == 200
    assert data["total_donations"] == 4
    assert data["distributed_donations"] == 2
    assert data["active_donations"] == 1
    assert data["cancelled_donations"] == 1
    assert data["quantity_by_unit"] == {"KG": 5.0, "MEALS": 24.0, "PACKETS": 2.0}
    assert data["distributed_quantity_by_unit"] == {"KG": 5.0, "MEALS": 20.0}
    assert data["food_type_breakdown"]["VEGETARIAN"] == 3
    assert data["food_type_breakdown"]["VEGAN"] == 1
    assert data["success_rate"] == 66.67


def test_zero_donation_donor_is_safe(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")

    response = client.get("/analytics/donor", headers=auth_header(donor_token))

    assert response.status_code == 200
    assert response.json()["total_donations"] == 0
    assert response.json()["success_rate"] == 0.0


def test_receiver_analytics_role_scope_and_completion(client: TestClient, db_session: Session) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    volunteer_token = register_and_login(client, "volunteer@example.com", "VOLUNTEER")
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    ngo_id = get_user_id(db_session, "ngo@example.com")
    volunteer_id = get_user_id(db_session, "volunteer@example.com")
    distributed_id = create_donation(client, donor_token, "Distributed Meals", quantity=30, quantity_unit="MEALS")["id"]
    collected_id = create_donation(client, donor_token, "Collected KG", quantity=8, quantity_unit="KG")["id"]
    other_id = create_donation(client, donor_token, "Other Receiver", quantity=99, quantity_unit="MEALS")["id"]
    set_donation_state(db_session, distributed_id, DonationStatus.DISTRIBUTED, accepted_by_user_id=ngo_id)
    set_donation_state(db_session, collected_id, DonationStatus.COLLECTED, accepted_by_user_id=ngo_id)
    set_donation_state(db_session, other_id, DonationStatus.DISTRIBUTED, accepted_by_user_id=volunteer_id)

    ngo_response = client.get("/analytics/receiver", headers=auth_header(ngo_token))
    volunteer_response = client.get("/analytics/receiver", headers=auth_header(volunteer_token))

    assert ngo_response.status_code == 200
    assert ngo_response.json()["total_accepted"] == 2
    assert ngo_response.json()["distributed"] == 1
    assert ngo_response.json()["collected"] == 1
    assert ngo_response.json()["completion_rate"] == 50.0
    assert ngo_response.json()["quantity_rescued_by_unit"] == {"MEALS": 30.0}
    assert volunteer_response.status_code == 200
    assert volunteer_response.json()["total_accepted"] == 1
    assert client.get("/analytics/receiver", headers=auth_header(admin_token)).status_code == 403


def test_receiver_zero_history_case(client: TestClient) -> None:
    volunteer_token = register_and_login(client, "volunteer@example.com", "VOLUNTEER")

    response = client.get("/analytics/receiver", headers=auth_header(volunteer_token))

    assert response.status_code == 200
    assert response.json()["total_accepted"] == 0
    assert response.json()["completion_rate"] == 0.0


def test_admin_analytics_and_breakdowns(client: TestClient, db_session: Session) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    ngo_id = get_user_id(db_session, "ngo@example.com")
    distributed_id = create_donation(client, donor_token, "Veg Meals", quantity=40, quantity_unit="MEALS", food_type="VEGETARIAN")["id"]
    cancelled_id = create_donation(client, donor_token, "Packets", quantity=10, quantity_unit="PACKETS", food_type="OTHER")["id"]
    expired_id = create_donation(client, donor_token, "Vegan KG", quantity=6, quantity_unit="KG", food_type="VEGAN")["id"]
    set_donation_state(db_session, distributed_id, DonationStatus.DISTRIBUTED, accepted_by_user_id=ngo_id)
    set_donation_state(db_session, cancelled_id, DonationStatus.CANCELLED)
    set_donation_state(db_session, expired_id, DonationStatus.EXPIRED)

    response = client.get("/analytics/admin", headers=auth_header(admin_token))
    blocked = client.get("/analytics/admin", headers=auth_header(ngo_token))
    data = response.json()

    assert response.status_code == 200
    assert blocked.status_code == 403
    assert data["total_users"] == 3
    assert data["total_donations"] == 3
    assert data["total_distributed"] == 1
    assert data["donations_by_status"]["DISTRIBUTED"] == 1
    assert data["donations_by_status"]["CANCELLED"] == 1
    assert data["food_type_breakdown"]["VEGETARIAN"] == 1
    assert data["quantity_distributed_by_unit"] == {"MEALS": 40.0}
    assert data["distribution_success_rate"] == 33.33


def test_empty_admin_analytics_works(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")

    response = client.get("/analytics/admin", headers=auth_header(admin_token))

    assert response.status_code == 200
    assert response.json()["total_donations"] == 0
    assert response.json()["distribution_success_rate"] == 0.0


def test_monthly_activity_groups_and_zero_months(client: TestClient, db_session: Session) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    donation_id = create_donation(client, donor_token, "April Meals")["id"]
    set_donation_state(db_session, donation_id, DonationStatus.DISTRIBUTED, created_at=datetime(2026, 4, 15, tzinfo=timezone.utc))

    response = client.get(
        "/analytics/admin?start_date=2026-04-01&end_date=2026-06-30",
        headers=auth_header(admin_token),
    )
    activity = {item["month"]: item for item in response.json()["monthly_donation_activity"]}

    assert response.status_code == 200
    assert activity["2026-04"]["created"] == 1
    assert activity["2026-04"]["distributed"] == 1
    assert activity["2026-05"]["created"] == 0
    assert activity["2026-06"]["distributed"] == 0


def test_invalid_admin_date_range_rejected(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")

    response = client.get(
        "/analytics/admin?start_date=2026-09-07&end_date=2026-01-01",
        headers=auth_header(admin_token),
    )

    assert response.status_code == 400


def test_admin_csv_export_permissions_headers_and_safety(client: TestClient, db_session: Session) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    ngo_id = get_user_id(db_session, "ngo@example.com")
    donation_id = create_donation(client, donor_token, "Export Meals")["id"]
    set_donation_state(db_session, donation_id, DonationStatus.DISTRIBUTED, accepted_by_user_id=ngo_id)

    blocked = client.get("/analytics/admin/export.csv", headers=auth_header(donor_token))
    response = client.get("/analytics/admin/export.csv", headers=auth_header(admin_token))

    assert blocked.status_code == 403
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "Donation ID,Food Name,Food Type,Quantity,Quantity Unit,Status,Created At,Accepted At,Collected At,Distributed At" in response.text
    assert "Export Meals" in response.text
    assert "password" not in response.text.lower()
    assert "secret" not in response.text.lower()


def test_csv_export_sanitizes_formula_like_values(client: TestClient, db_session: Session) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    ngo_id = get_user_id(db_session, "ngo@example.com")
    donation_id = create_donation(client, donor_token, "=HYPERLINK(\"http://bad.example\")")["id"]
    set_donation_state(db_session, donation_id, DonationStatus.DISTRIBUTED, accepted_by_user_id=ngo_id)

    response = client.get("/analytics/admin/export.csv", headers=auth_header(admin_token))

    assert response.status_code == 200
    assert "'=HYPERLINK" in response.text
    assert ",=HYPERLINK" not in response.text
