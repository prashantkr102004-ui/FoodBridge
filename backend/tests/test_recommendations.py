from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.donation import Donation, DonationStatus
from app.models.user import User
from app.services.recommendation_service import (
    calculate_distance_score,
    calculate_match_score,
    calculate_urgency_score,
)
from tests.test_donations import create_test_admin


def registration_payload(email: str, role: str, latitude: float | None = None, longitude: float | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": f"{role.title()} User",
        "email": email,
        "phone": "9876543210",
        "password": "strongpass123",
        "role": role,
        "organization_name": f"{role.title()} Organization",
        "location": "Pune",
    }
    if latitude is not None:
        payload["latitude"] = latitude
    if longitude is not None:
        payload["longitude"] = longitude
    return payload


def register_and_login(
    client: TestClient,
    email: str,
    role: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> str:
    if role == "ADMIN":
        create_test_admin(email)
    else:
        client.post("/auth/register", json=registration_payload(email, role, latitude, longitude))
    response = client.post("/auth/login", json={"email": email, "password": "strongpass123"})
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def donation_payload(
    food_name: str,
    food_type: str = "VEGETARIAN",
    quantity: float = 25,
    quantity_unit: str = "MEALS",
    latitude: float | None = 18.5204,
    longitude: float | None = 73.8567,
    available_until: datetime | None = None,
) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    payload: dict[str, object] = {
        "food_name": food_name,
        "food_type": food_type,
        "quantity": quantity,
        "quantity_unit": quantity_unit,
        "description": "Freshly packed food",
        "prepared_at": now.isoformat(),
        "available_until": (available_until or now + timedelta(hours=3)).isoformat(),
        "pickup_address": "College Canteen, Pune",
        "image_url": None,
    }
    if latitude is not None:
        payload["latitude"] = latitude
    if longitude is not None:
        payload["longitude"] = longitude
    return payload


def create_donation(
    client: TestClient,
    donor_token: str,
    food_name: str,
    food_type: str = "VEGETARIAN",
    quantity: float = 25,
    quantity_unit: str = "MEALS",
    latitude: float | None = 18.5204,
    longitude: float | None = 73.8567,
    available_until: datetime | None = None,
) -> dict:
    response = client.post(
        "/donations",
        json=donation_payload(
            food_name=food_name,
            food_type=food_type,
            quantity=quantity,
            quantity_unit=quantity_unit,
            latitude=latitude,
            longitude=longitude,
            available_until=available_until,
        ),
        headers=auth_header(donor_token),
    )
    assert response.status_code == 201
    return response.json()


def set_donation_state(
    db: Session,
    donation_id: str,
    status: DonationStatus,
    accepted_by_user_id: str | None = None,
    available_until: datetime | None = None,
) -> None:
    donation = db.get(Donation, donation_id)
    donation.status = status.value
    donation.accepted_by_user_id = accepted_by_user_id
    if available_until is not None:
        donation.available_until = available_until
    db.add(donation)
    db.commit()


def get_user_id(db: Session, email: str) -> str:
    return db.query(User).filter(User.email == email).one().id


def test_ngo_can_access_recommendations(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    create_donation(client, donor_token, "Veg Meals")

    response = client.get("/recommendations/donations", headers=auth_header(ngo_token))

    assert response.status_code == 200
    assert response.json()[0]["food_name"] == "Veg Meals"


def test_volunteer_can_access_recommendations(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    volunteer_token = register_and_login(client, "volunteer@example.com", "VOLUNTEER", latitude=18.5204, longitude=73.8567)
    create_donation(client, donor_token, "Rice Packs")

    response = client.get("/recommendations/donations", headers=auth_header(volunteer_token))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_donor_admin_and_unauthenticated_users_are_blocked(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR", latitude=18.5204, longitude=73.8567)
    admin_token = register_and_login(client, "admin@example.com", "ADMIN", latitude=18.5204, longitude=73.8567)

    assert client.get("/recommendations/donations", headers=auth_header(donor_token)).status_code == 403
    assert client.get("/recommendations/donations", headers=auth_header(admin_token)).status_code == 403
    assert client.get("/recommendations/donations").status_code == 401


def test_missing_receiver_coordinates_returns_clear_error(client: TestClient) -> None:
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")

    response = client.get("/recommendations/donations", headers=auth_header(ngo_token))

    assert response.status_code == 400
    assert response.json()["detail"] == "Set your location before using smart recommendations."


def test_unavailable_or_locationless_donations_are_excluded(client: TestClient, db_session: Session) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    expired_id = create_donation(client, donor_token, "Expired Food")["id"]
    cancelled_id = create_donation(client, donor_token, "Cancelled Food")["id"]
    accepted_id = create_donation(client, donor_token, "Accepted Food")["id"]
    create_donation(client, donor_token, "No Coordinates", latitude=None, longitude=None)
    set_donation_state(db_session, expired_id, DonationStatus.AVAILABLE, available_until=datetime.now(timezone.utc) - timedelta(hours=1))
    set_donation_state(db_session, cancelled_id, DonationStatus.CANCELLED)
    set_donation_state(db_session, accepted_id, DonationStatus.ACCEPTED)

    response = client.get("/recommendations/donations", headers=auth_header(ngo_token))

    assert response.status_code == 200
    assert response.json() == []


def test_distance_and_urgency_score_helpers() -> None:
    now = datetime.now(timezone.utc)

    assert calculate_distance_score(distance_km=1, radius_km=10) > calculate_distance_score(distance_km=8, radius_km=10)
    assert calculate_urgency_score(now + timedelta(minutes=45), now) > calculate_urgency_score(now + timedelta(hours=6), now)
    assert 0 <= calculate_match_score(100, 100, 100, 100) <= 100


def test_results_are_sorted_by_match_score_descending(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    create_donation(client, donor_token, "Lower Match", quantity=5, latitude=18.65, longitude=73.95, available_until=datetime.now(timezone.utc) + timedelta(hours=8))
    create_donation(client, donor_token, "Higher Match", quantity=50, latitude=18.521, longitude=73.857, available_until=datetime.now(timezone.utc) + timedelta(minutes=45))

    response = client.get("/recommendations/donations", headers=auth_header(ngo_token))
    results = response.json()

    assert response.status_code == 200
    assert [item["food_name"] for item in results] == ["Higher Match", "Lower Match"]
    assert results[0]["match_score"] >= results[1]["match_score"]
    assert all(0 <= item["match_score"] <= 100 for item in results)


def test_radius_and_food_type_filters_work(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    create_donation(client, donor_token, "Nearby Veg", food_type="VEGETARIAN", latitude=18.521, longitude=73.857)
    create_donation(client, donor_token, "Nearby Vegan", food_type="VEGAN", latitude=18.522, longitude=73.858)
    create_donation(client, donor_token, "Far Veg", food_type="VEGETARIAN", latitude=19.076, longitude=72.8777)

    response = client.get(
        "/recommendations/donations?radius_km=5&food_type=VEGETARIAN",
        headers=auth_header(ngo_token),
    )

    assert response.status_code == 200
    assert [item["food_name"] for item in response.json()] == ["Nearby Veg"]


def test_new_user_with_no_history_still_receives_recommendations(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "new-ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    create_donation(client, donor_token, "Fresh Meals")

    response = client.get("/recommendations/donations", headers=auth_header(ngo_token))

    assert response.status_code == 200
    assert response.json()[0]["score_breakdown"]["preference"] == 70


def test_preference_scoring_uses_sufficient_history(client: TestClient, db_session: Session) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    ngo_id = get_user_id(db_session, "ngo@example.com")
    for index in range(3):
        donation_id = create_donation(client, donor_token, f"History Veg {index}", food_type="VEGETARIAN")["id"]
        set_donation_state(db_session, donation_id, DonationStatus.DISTRIBUTED, accepted_by_user_id=ngo_id)
    create_donation(client, donor_token, "Recommended Veg", food_type="VEGETARIAN", latitude=18.521, longitude=73.857)
    create_donation(client, donor_token, "Less Preferred Vegan", food_type="VEGAN", latitude=18.521, longitude=73.857)

    response = client.get("/recommendations/donations", headers=auth_header(ngo_token))
    by_name = {item["food_name"]: item for item in response.json()}

    assert by_name["Recommended Veg"]["score_breakdown"]["preference"] > by_name["Less Preferred Vegan"]["score_breakdown"]["preference"]
    assert "Matches your commonly accepted food type" in by_name["Recommended Veg"]["reasons"]


def test_recommendation_reasons_match_real_factors(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    create_donation(
        client,
        donor_token,
        "Urgent Nearby Meals",
        quantity=80,
        latitude=18.521,
        longitude=73.857,
        available_until=datetime.now(timezone.utc) + timedelta(minutes=45),
    )

    response = client.get("/recommendations/donations", headers=auth_header(ngo_token))
    reasons = response.json()[0]["reasons"]

    assert any("km away" in reason for reason in reasons)
    assert "Expires within 60 minutes" in reasons
    assert "Large available quantity" in reasons


def test_accepted_donation_disappears_from_recommendations(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    donation_id = create_donation(client, donor_token, "Accept Me")["id"]

    before_accept = client.get("/recommendations/donations", headers=auth_header(ngo_token))
    accept_response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_token))
    after_accept = client.get("/recommendations/donations", headers=auth_header(ngo_token))

    assert before_accept.status_code == 200
    assert len(before_accept.json()) == 1
    assert accept_response.status_code == 200
    assert after_accept.json() == []
