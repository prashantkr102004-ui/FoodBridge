from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.donation import Donation
from tests.test_donations import auth_header, create_donation, donation_payload, register_and_login


def expire_donation_directly(db: Session, donation_id: str) -> None:
    donation = db.get(Donation, donation_id)
    donation.available_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.add(donation)
    db.commit()


def test_ngo_successfully_accepts_available_donation(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]

    response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_token))
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ACCEPTED"
    assert data["accepted_by_user_id"]
    assert data["accepted_at"]
    assert data["donor_phone"] == "9876543210"


def test_volunteer_successfully_accepts_available_donation(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    volunteer_token = register_and_login(client, "volunteer@example.com", "VOLUNTEER")
    donation_id = create_donation(client, donor_token).json()["id"]

    response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(volunteer_token))

    assert response.status_code == 200
    assert response.json()["status"] == "ACCEPTED"


def test_donor_cannot_accept_donation(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    donation_id = create_donation(client, donor_token).json()["id"]

    response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(donor_token))

    assert response.status_code == 403


def test_admin_cannot_accept_through_normal_endpoint(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    donation_id = create_donation(client, donor_token).json()["id"]

    response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(admin_token))

    assert response.status_code == 403


def test_unauthenticated_user_cannot_accept(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    donation_id = create_donation(client, donor_token).json()["id"]

    response = client.post(f"/donations/{donation_id}/accept")

    assert response.status_code == 401


def test_cannot_accept_expired_donation(client: TestClient, db_session: Session) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]
    expire_donation_directly(db_session, donation_id)
    client.get(f"/donations/{donation_id}", headers=auth_header(ngo_token))

    response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_token))

    assert response.status_code == 409


def test_cannot_accept_cancelled_donation(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]
    client.post(f"/donations/{donation_id}/cancel", headers=auth_header(donor_token))

    response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_token))

    assert response.status_code == 409


def test_cannot_accept_already_accepted_donation(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_a_token = register_and_login(client, "ngo-a@example.com", "NGO")
    ngo_b_token = register_and_login(client, "ngo-b@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]
    client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_a_token))

    response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_b_token))

    assert response.status_code == 409


def test_accepted_donation_status_and_fields_are_stored(
    client: TestClient,
    db_session: Session,
) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]

    response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_token))
    accepted_by_user_id = response.json()["accepted_by_user_id"]
    db_session.expire_all()
    donation = db_session.get(Donation, donation_id)

    assert response.status_code == 200
    assert donation.status == "ACCEPTED"
    assert donation.accepted_by_user_id == accepted_by_user_id
    assert donation.accepted_at is not None


def test_ngo_can_view_their_accepted_donations(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]
    client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_token))

    response = client.get("/donations/accepted/my", headers=auth_header(ngo_token))

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == donation_id
    assert response.json()[0]["donor_phone"] == "9876543210"


def test_ngo_a_does_not_see_ngo_b_accepted_items(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_a_token = register_and_login(client, "ngo-a@example.com", "NGO")
    ngo_b_token = register_and_login(client, "ngo-b@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]
    client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_b_token))

    response = client.get("/donations/accepted/my", headers=auth_header(ngo_a_token))

    assert response.status_code == 200
    assert response.json() == []


def test_donor_can_see_own_donation_was_accepted(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]
    client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_token))

    response = client.get(f"/donations/{donation_id}", headers=auth_header(donor_token))
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ACCEPTED"
    assert data["accepted_at"]
    assert data["accepted_by_name"] == "Ngo User"
    assert data["donor_phone"] is None


def test_unrelated_donor_does_not_see_private_acceptance_details(client: TestClient) -> None:
    donor_a_token = register_and_login(client, "donor-a@example.com", "DONOR")
    donor_b_token = register_and_login(client, "donor-b@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_a_token).json()["id"]
    client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_token))

    response = client.get(f"/donations/{donation_id}", headers=auth_header(donor_b_token))
    data = response.json()

    assert response.status_code == 200
    assert data["accepted_by_name"] is None
    assert data["donor_phone"] is None


def test_unrelated_receiver_does_not_see_private_donor_contact_details(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_a_token = register_and_login(client, "ngo-a@example.com", "NGO")
    ngo_b_token = register_and_login(client, "ngo-b@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]
    client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_a_token))

    response = client.get(f"/donations/{donation_id}", headers=auth_header(ngo_b_token))
    data = response.json()

    assert response.status_code == 200
    assert data["donor_name"] is None
    assert data["donor_phone"] is None


def test_expired_stale_available_donation_cannot_be_accepted(
    client: TestClient,
    db_session: Session,
) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]
    expire_donation_directly(db_session, donation_id)

    response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_token))

    assert response.status_code == 409


def test_double_acceptance_allows_only_one_successful_accepter(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_a_token = register_and_login(client, "ngo-a@example.com", "NGO")
    ngo_b_token = register_and_login(client, "ngo-b@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]

    first_response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_a_token))
    second_response = client.post(f"/donations/{donation_id}/accept", headers=auth_header(ngo_b_token))

    statuses = sorted([first_response.status_code, second_response.status_code])
    assert statuses == [200, 409]
