from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.donation import Donation
from app.models.user import User
from app.utils.security import hash_password
from conftest import TestingSessionLocal


def registration_payload(email: str, role: str) -> dict[str, str]:
    return {
        "name": f"{role.title()} User",
        "email": email,
        "phone": "9876543210",
        "password": "strongpass123",
        "role": role,
        "organization_name": f"{role.title()} Organization",
        "location": "Pune",
    }


def register_and_login(client: TestClient, email: str, role: str) -> str:
    if role == "ADMIN":
        create_test_admin(email)
    else:
        client.post("/auth/register", json=registration_payload(email, role))
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "strongpass123"},
    )
    return response.json()["access_token"]


def create_test_admin(email: str = "admin@example.com") -> None:
    db = TestingSessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing is None:
            db.add(
                User(
                    name="Admin User",
                    email=email,
                    phone="9876543210",
                    password_hash=hash_password("strongpass123"),
                    role="ADMIN",
                    organization_name="Admin Organization",
                    location="Pune",
                    is_active=True,
                )
            )
            db.commit()
    finally:
        db.close()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def donation_payload(
    food_name: str = "Vegetable Rice",
    quantity: float = 25,
    available_until: datetime | None = None,
) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    return {
        "food_name": food_name,
        "food_type": "VEGETARIAN",
        "quantity": quantity,
        "quantity_unit": "MEALS",
        "description": "Freshly prepared lunch boxes",
        "prepared_at": now.isoformat(),
        "available_until": (available_until or now + timedelta(hours=3)).isoformat(),
        "pickup_address": "College Canteen, Pune",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "image_url": "https://example.com/food.jpg",
    }


def create_donation(client: TestClient, token: str, food_name: str = "Vegetable Rice"):
    return client.post(
        "/donations",
        json=donation_payload(food_name=food_name),
        headers=auth_header(token),
    )


def expire_donation_directly(db: Session, donation_id: str) -> None:
    donation = db.get(Donation, donation_id)
    donation.available_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.add(donation)
    db.commit()


def test_donor_creates_donation_successfully(client: TestClient) -> None:
    token = register_and_login(client, "donor@example.com", "DONOR")

    response = create_donation(client, token)
    data = response.json()

    assert response.status_code == 201
    assert data["food_name"] == "Vegetable Rice"
    assert data["status"] == "AVAILABLE"
    assert data["donor_id"]


def test_ngo_cannot_create_donation(client: TestClient) -> None:
    token = register_and_login(client, "ngo@example.com", "NGO")

    response = client.post("/donations", json=donation_payload(), headers=auth_header(token))

    assert response.status_code == 403


def test_volunteer_cannot_create_donation(client: TestClient) -> None:
    token = register_and_login(client, "volunteer@example.com", "VOLUNTEER")

    response = client.post("/donations", json=donation_payload(), headers=auth_header(token))

    assert response.status_code == 403


def test_unauthenticated_user_cannot_create_donation(client: TestClient) -> None:
    response = client.post("/donations", json=donation_payload())

    assert response.status_code == 401


def test_invalid_quantity_is_rejected(client: TestClient) -> None:
    token = register_and_login(client, "donor@example.com", "DONOR")

    response = client.post(
        "/donations",
        json=donation_payload(quantity=0),
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_expired_available_until_is_rejected(client: TestClient) -> None:
    token = register_and_login(client, "donor@example.com", "DONOR")
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)

    response = client.post(
        "/donations",
        json=donation_payload(available_until=past_time),
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_donor_can_view_own_donations(client: TestClient) -> None:
    token = register_and_login(client, "donor@example.com", "DONOR")
    create_donation(client, token)

    response = client.get("/donations/my", headers=auth_header(token))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_available_donations_can_be_listed(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    create_donation(client, donor_token)

    response = client.get("/donations", headers=auth_header(ngo_token))

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "AVAILABLE"


def test_donor_can_update_own_available_donation(client: TestClient) -> None:
    token = register_and_login(client, "donor@example.com", "DONOR")
    donation_id = create_donation(client, token).json()["id"]

    response = client.patch(
        f"/donations/{donation_id}",
        json={"food_name": "Chapati and Curry", "quantity": 40},
        headers=auth_header(token),
    )
    data = response.json()

    assert response.status_code == 200
    assert data["food_name"] == "Chapati and Curry"
    assert data["quantity"] == 40


def test_donor_cannot_update_another_donors_donation(client: TestClient) -> None:
    donor_a_token = register_and_login(client, "donor-a@example.com", "DONOR")
    donor_b_token = register_and_login(client, "donor-b@example.com", "DONOR")
    donation_id = create_donation(client, donor_a_token).json()["id"]

    response = client.patch(
        f"/donations/{donation_id}",
        json={"food_name": "Not allowed"},
        headers=auth_header(donor_b_token),
    )

    assert response.status_code == 403


def test_donor_can_cancel_own_donation(client: TestClient) -> None:
    token = register_and_login(client, "donor@example.com", "DONOR")
    donation_id = create_donation(client, token).json()["id"]

    response = client.post(f"/donations/{donation_id}/cancel", headers=auth_header(token))

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_donor_cannot_cancel_another_donors_donation(client: TestClient) -> None:
    donor_a_token = register_and_login(client, "donor-a@example.com", "DONOR")
    donor_b_token = register_and_login(client, "donor-b@example.com", "DONOR")
    donation_id = create_donation(client, donor_a_token).json()["id"]

    response = client.post(f"/donations/{donation_id}/cancel", headers=auth_header(donor_b_token))

    assert response.status_code == 403


def test_cancelled_donation_is_not_shown_in_available_list(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]
    client.post(f"/donations/{donation_id}/cancel", headers=auth_header(donor_token))

    response = client.get("/donations", headers=auth_header(ngo_token))

    assert response.status_code == 200
    assert response.json() == []


def test_expired_donation_is_not_shown_in_available_list(
    client: TestClient,
    db_session: Session,
) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]
    expire_donation_directly(db_session, donation_id)

    response = client.get("/donations", headers=auth_header(ngo_token))

    assert response.status_code == 200
    assert response.json() == []


def test_cannot_edit_cancelled_donation(client: TestClient) -> None:
    token = register_and_login(client, "donor@example.com", "DONOR")
    donation_id = create_donation(client, token).json()["id"]
    client.post(f"/donations/{donation_id}/cancel", headers=auth_header(token))

    response = client.patch(
        f"/donations/{donation_id}",
        json={"food_name": "Too late"},
        headers=auth_header(token),
    )

    assert response.status_code == 409


def test_missing_donation_returns_404(client: TestClient) -> None:
    token = register_and_login(client, "donor@example.com", "DONOR")

    response = client.get("/donations/missing-id", headers=auth_header(token))

    assert response.status_code == 404
