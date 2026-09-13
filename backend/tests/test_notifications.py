from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.donation import Donation, DonationStatus
from app.models.notification import Notification
from app.models.user import User


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
    client.post("/auth/register", json=registration_payload(email, role))
    response = client.post("/auth/login", json={"email": email, "password": "strongpass123"})
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def donation_payload(food_name: str = "Veg Biryani") -> dict[str, object]:
    now = datetime.now(timezone.utc)
    return {
        "food_name": food_name,
        "food_type": "VEGETARIAN",
        "quantity": 25,
        "quantity_unit": "MEALS",
        "description": "Fresh food",
        "prepared_at": now.isoformat(),
        "available_until": (now + timedelta(hours=3)).isoformat(),
        "pickup_address": "College Canteen, Pune",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "image_url": None,
    }


def create_donation(client: TestClient, donor_token: str, food_name: str = "Veg Biryani") -> dict:
    response = client.post("/donations", json=donation_payload(food_name), headers=auth_header(donor_token))
    assert response.status_code == 201
    return response.json()


def notification_count(db: Session, user_id: str, donation_id: str, notification_type: str) -> int:
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.donation_id == donation_id,
            Notification.type == notification_type,
        )
        .count()
    )


def user_id(db: Session, email: str) -> str:
    return db.query(User).filter(User.email == email).one().id


def accept_donation(client: TestClient, donation_id: str, receiver_token: str) -> dict:
    response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(receiver_token))
    assert response.status_code == 200
    return response.json()


def collect_donation(client: TestClient, donation_id: str, receiver_token: str) -> dict:
    response = client.post(f"/donations/{donation_id}/collect", headers=auth_header(receiver_token))
    assert response.status_code == 200
    return response.json()


def distribute_donation(client: TestClient, donation_id: str, receiver_token: str) -> dict:
    response = client.post(f"/donations/{donation_id}/distribute", headers=auth_header(receiver_token))
    assert response.status_code == 200
    return response.json()


def test_donor_receives_notification_after_ngo_accepts(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation = create_donation(client, donor_token)

    accept_donation(client, donation["id"], ngo_token)
    response = client.get("/notifications", headers=auth_header(donor_token))

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["type"] == "DONATION_ACCEPTED"
    assert item["donation_id"] == donation["id"]
    assert "Veg Biryani" in item["message"]
    assert "Ngo Organization" in item["message"]


def test_donor_receives_notification_after_volunteer_accepts(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    volunteer_token = register_and_login(client, "volunteer@example.com", "VOLUNTEER")
    donation = create_donation(client, donor_token)

    accept_donation(client, donation["id"], volunteer_token)
    response = client.get("/notifications", headers=auth_header(donor_token))

    assert response.status_code == 200
    assert response.json()["items"][0]["type"] == "DONATION_ACCEPTED"


def test_donor_receives_collection_and_distribution_notifications(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation = create_donation(client, donor_token)

    accept_donation(client, donation["id"], ngo_token)
    collect_donation(client, donation["id"], ngo_token)
    distribute_donation(client, donation["id"], ngo_token)
    response = client.get("/notifications", headers=auth_header(donor_token))
    types = [item["type"] for item in response.json()["items"]]

    assert "DONATION_COLLECTED" in types
    assert "DONATION_DISTRIBUTED" in types


def test_expiry_creates_one_notification(client: TestClient, db_session: Session) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    donation = create_donation(client, donor_token)
    donor_id = user_id(db_session, "donor@example.com")
    db_donation = db_session.get(Donation, donation["id"])
    db_donation.available_until = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.add(db_donation)
    db_session.commit()

    first = client.get(f"/donations/{donation['id']}", headers=auth_header(donor_token))
    second = client.get(f"/donations/{donation['id']}", headers=auth_header(donor_token))

    assert first.status_code == 200
    assert second.status_code == 200
    assert notification_count(db_session, donor_id, donation["id"], "DONATION_EXPIRED") == 1


def test_failed_lifecycle_actions_do_not_create_notifications(client: TestClient, db_session: Session) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation = create_donation(client, donor_token)
    donor_id = user_id(db_session, "donor@example.com")

    client.post(f"/donations/{donation['id']}/cancel", headers=auth_header(donor_token))
    failed_accept = client.post(f"/donations/{donation['id']}/accept", headers=auth_header(ngo_token))
    failed_collect = client.post(f"/donations/{donation['id']}/collect", headers=auth_header(ngo_token))
    failed_distribute = client.post(f"/donations/{donation['id']}/distribute", headers=auth_header(ngo_token))

    assert failed_accept.status_code == 409
    assert failed_collect.status_code == 409
    assert failed_distribute.status_code == 409
    assert db_session.query(Notification).filter(Notification.user_id == donor_id).count() == 0


def test_current_user_lists_only_own_notifications(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    other_donor_token = register_and_login(client, "other-donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation = create_donation(client, donor_token)

    accept_donation(client, donation["id"], ngo_token)
    donor_response = client.get("/notifications", headers=auth_header(donor_token))
    other_response = client.get("/notifications", headers=auth_header(other_donor_token))

    assert donor_response.json()["total"] == 1
    assert other_response.json()["total"] == 0


def test_notifications_order_unread_filter_and_count(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation = create_donation(client, donor_token)

    accept_donation(client, donation["id"], ngo_token)
    collect_donation(client, donation["id"], ngo_token)
    response = client.get("/notifications", headers=auth_header(donor_token))
    unread_response = client.get("/notifications?unread_only=true", headers=auth_header(donor_token))
    count_response = client.get("/notifications/unread-count", headers=auth_header(donor_token))

    items = response.json()["items"]
    assert items[0]["type"] == "DONATION_COLLECTED"
    assert unread_response.json()["total"] == 2
    assert count_response.json()["unread_count"] == 2


def test_mark_one_read_is_idempotent_and_private(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    other_token = register_and_login(client, "other@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation = create_donation(client, donor_token)
    accept_donation(client, donation["id"], ngo_token)
    notification_id = client.get("/notifications", headers=auth_header(donor_token)).json()["items"][0]["id"]

    other_response = client.post(f"/notifications/{notification_id}/read", headers=auth_header(other_token))
    first = client.post(f"/notifications/{notification_id}/read", headers=auth_header(donor_token))
    read_at = first.json()["read_at"]
    second = client.post(f"/notifications/{notification_id}/read", headers=auth_header(donor_token))

    assert other_response.status_code == 404
    assert first.status_code == 200
    assert first.json()["is_read"] is True
    assert read_at is not None
    assert second.json()["read_at"] == read_at


def test_mark_all_read_affects_only_current_user(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    other_donor_token = register_and_login(client, "other@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation = create_donation(client, donor_token)
    other_donation = create_donation(client, other_donor_token, "Other Food")
    accept_donation(client, donation["id"], ngo_token)
    accept_donation(client, other_donation["id"], ngo_token)

    response = client.post("/notifications/read-all", headers=auth_header(donor_token))
    donor_count = client.get("/notifications/unread-count", headers=auth_header(donor_token))
    other_count = client.get("/notifications/unread-count", headers=auth_header(other_donor_token))

    assert response.status_code == 200
    assert response.json()["updated"] == 1
    assert donor_count.json()["unread_count"] == 0
    assert other_count.json()["unread_count"] == 1


def test_notification_pagination(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    for index in range(3):
        donation = create_donation(client, donor_token, f"Food {index}")
        accept_donation(client, donation["id"], ngo_token)

    response = client.get("/notifications?page=1&page_size=2", headers=auth_header(donor_token))

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert response.json()["page"] == 1
    assert len(response.json()["items"]) == 2


def test_duplicate_lifecycle_requests_create_only_one_donor_notification(client: TestClient, db_session: Session) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    other_ngo_token = register_and_login(client, "other-ngo@example.com", "NGO")
    donation = create_donation(client, donor_token)
    donor_id = user_id(db_session, "donor@example.com")

    assert client.post(f"/donations/{donation['id']}/accept", headers=auth_header(ngo_token)).status_code == 200
    assert client.post(f"/donations/{donation['id']}/accept", headers=auth_header(other_ngo_token)).status_code == 409
    assert client.post(f"/donations/{donation['id']}/collect", headers=auth_header(ngo_token)).status_code == 200
    assert client.post(f"/donations/{donation['id']}/collect", headers=auth_header(ngo_token)).status_code == 409
    assert client.post(f"/donations/{donation['id']}/distribute", headers=auth_header(ngo_token)).status_code == 200
    assert client.post(f"/donations/{donation['id']}/distribute", headers=auth_header(ngo_token)).status_code == 409

    assert notification_count(db_session, donor_id, donation["id"], "DONATION_ACCEPTED") == 1
    assert notification_count(db_session, donor_id, donation["id"], "DONATION_COLLECTED") == 1
    assert notification_count(db_session, donor_id, donation["id"], "DONATION_DISTRIBUTED") == 1
