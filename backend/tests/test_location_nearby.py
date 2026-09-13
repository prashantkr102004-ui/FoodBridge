from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.donation import Donation, DonationStatus
from app.models.user import User
from app.utils.location import haversine_distance_km


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
    client.post("/auth/register", json=registration_payload(email, role, latitude, longitude))
    response = client.post("/auth/login", json={"email": email, "password": "strongpass123"})
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def donation_payload(
    food_name: str = "Vegetable Rice",
    latitude: float | None = 18.5204,
    longitude: float | None = 73.8567,
    available_until: datetime | None = None,
) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    payload: dict[str, object] = {
        "food_name": food_name,
        "food_type": "VEGETARIAN",
        "quantity": 25,
        "quantity_unit": "MEALS",
        "description": "Fresh food",
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
    latitude: float | None = 18.5204,
    longitude: float | None = 73.8567,
) -> dict:
    response = client.post(
        "/donations",
        json=donation_payload(food_name=food_name, latitude=latitude, longitude=longitude),
        headers=auth_header(donor_token),
    )
    assert response.status_code == 201
    return response.json()


def set_donation_status(db: Session, donation_id: str, status: DonationStatus) -> None:
    donation = db.get(Donation, donation_id)
    donation.status = status.value
    db.add(donation)
    db.commit()


def test_valid_coordinates_are_accepted_for_registration(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json=registration_payload("ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567),
    )

    assert response.status_code == 201
    assert response.json()["latitude"] == 18.5204
    assert response.json()["longitude"] == 73.8567


def test_invalid_latitude_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json=registration_payload("ngo@example.com", "NGO", latitude=91, longitude=73.8567),
    )

    assert response.status_code == 422


def test_invalid_longitude_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json=registration_payload("ngo@example.com", "NGO", latitude=18.5204, longitude=181),
    )

    assert response.status_code == 422


def test_invalid_donation_latitude_is_rejected(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")

    response = client.post(
        "/donations",
        json=donation_payload(latitude=-91, longitude=73.8567),
        headers=auth_header(donor_token),
    )

    assert response.status_code == 422


def test_invalid_donation_longitude_is_rejected(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")

    response = client.post(
        "/donations",
        json=donation_payload(latitude=18.5204, longitude=181),
        headers=auth_header(donor_token),
    )

    assert response.status_code == 422


def test_partial_donation_coordinates_are_rejected(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")

    response = client.post(
        "/donations",
        json=donation_payload(latitude=18.5204, longitude=None),
        headers=auth_header(donor_token),
    )

    assert response.status_code == 422


def test_user_can_update_own_location(client: TestClient) -> None:
    token = register_and_login(client, "receiver@example.com", "NGO")

    response = client.patch(
        "/users/me/location",
        json={"location": "Mumbai", "latitude": 19.076, "longitude": 72.8777},
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["location"] == "Mumbai"
    assert response.json()["latitude"] == 19.076


def test_user_cannot_update_another_users_location(client: TestClient, db_session: Session) -> None:
    token = register_and_login(client, "receiver-a@example.com", "NGO")
    register_and_login(client, "receiver-b@example.com", "NGO")

    response = client.patch(
        "/users/me/location",
        json={"location": "Mumbai", "latitude": 19.076, "longitude": 72.8777},
        headers=auth_header(token),
    )
    other_user = db_session.query(User).filter(User.email == "receiver-b@example.com").one()

    assert response.status_code == 200
    assert other_user.location == "Pune"
    assert other_user.latitude is None


def test_nearby_endpoint_blocked_for_unauthenticated_user(client: TestClient) -> None:
    response = client.get("/donations/nearby")

    assert response.status_code == 401


def test_nearby_endpoint_allowed_for_ngo(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    create_donation(client, donor_token, "Nearby Rice")

    response = client.get("/donations/nearby", headers=auth_header(ngo_token))

    assert response.status_code == 200
    assert response.json()[0]["food_name"] == "Nearby Rice"


def test_nearby_endpoint_allowed_for_volunteer(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    volunteer_token = register_and_login(
        client,
        "volunteer@example.com",
        "VOLUNTEER",
        latitude=18.5204,
        longitude=73.8567,
    )
    create_donation(client, donor_token, "Nearby Meals")

    response = client.get("/donations/nearby", headers=auth_header(volunteer_token))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_donor_cannot_use_receiver_nearby_endpoint(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR", latitude=18.5204, longitude=73.8567)

    response = client.get("/donations/nearby", headers=auth_header(donor_token))

    assert response.status_code == 403


def test_user_without_location_receives_clear_error(client: TestClient) -> None:
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")

    response = client.get("/donations/nearby", headers=auth_header(ngo_token))

    assert response.status_code == 400
    assert response.json()["detail"] == "Set your location before using nearby donations."


def test_nearby_donations_are_sorted_nearest_first(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    create_donation(client, donor_token, "Far Food", latitude=19.076, longitude=72.8777)
    create_donation(client, donor_token, "Near Food", latitude=18.521, longitude=73.857)

    response = client.get("/donations/nearby", headers=auth_header(ngo_token))
    names = [item["food_name"] for item in response.json()]

    assert response.status_code == 200
    assert names == ["Near Food", "Far Food"]


def test_radius_filtering_works(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    create_donation(client, donor_token, "Near Food", latitude=18.521, longitude=73.857)
    create_donation(client, donor_token, "Far Food", latitude=19.076, longitude=72.8777)

    response = client.get("/donations/nearby?radius_km=5", headers=auth_header(ngo_token))

    assert response.status_code == 200
    assert [item["food_name"] for item in response.json()] == ["Near Food"]


def test_expired_cancelled_and_accepted_donations_are_excluded(
    client: TestClient,
    db_session: Session,
) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    expired_id = create_donation(client, donor_token, "Expired Food")["id"]
    cancelled_id = create_donation(client, donor_token, "Cancelled Food")["id"]
    accepted_id = create_donation(client, donor_token, "Accepted Food")["id"]
    set_donation_status(db_session, expired_id, DonationStatus.EXPIRED)
    set_donation_status(db_session, cancelled_id, DonationStatus.CANCELLED)
    set_donation_status(db_session, accepted_id, DonationStatus.ACCEPTED)

    response = client.get("/donations/nearby", headers=auth_header(ngo_token))

    assert response.status_code == 200
    assert response.json() == []


def test_donation_without_coordinates_excluded_from_nearby_but_in_normal_list(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO", latitude=18.5204, longitude=73.8567)
    create_donation(client, donor_token, "Address Only Food", latitude=None, longitude=None)

    nearby_response = client.get("/donations/nearby", headers=auth_header(ngo_token))
    normal_response = client.get("/donations", headers=auth_header(ngo_token))

    assert nearby_response.status_code == 200
    assert nearby_response.json() == []
    assert normal_response.status_code == 200
    assert normal_response.json()[0]["food_name"] == "Address Only Food"


def test_haversine_calculation_returns_approximate_distance() -> None:
    distance = haversine_distance_km(18.5204, 73.8567, 19.076, 72.8777)

    assert 115 <= distance <= 130
