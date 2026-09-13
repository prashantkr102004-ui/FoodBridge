from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.donation import Donation
from tests.test_donations import auth_header, create_donation, register_and_login


def accept_donation(client: TestClient, donation_id: str, token: str):
    return client.post(f"/donations/{donation_id}/accept", headers=auth_header(token))


def collect_donation(client: TestClient, donation_id: str, token: str):
    return client.post(f"/donations/{donation_id}/collect", headers=auth_header(token))


def distribute_donation(client: TestClient, donation_id: str, token: str):
    return client.post(f"/donations/{donation_id}/distribute", headers=auth_header(token))


def create_accepted_donation(client: TestClient, accepter_role: str = "NGO") -> tuple[str, str, str]:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    accepter_email = f"{accepter_role.lower()}@example.com"
    accepter_token = register_and_login(client, accepter_email, accepter_role)
    donation_id = create_donation(client, donor_token).json()["id"]
    accept_donation(client, donation_id, accepter_token)
    return donation_id, donor_token, accepter_token


def create_collected_donation(client: TestClient, accepter_role: str = "NGO") -> tuple[str, str, str]:
    donation_id, donor_token, accepter_token = create_accepted_donation(client, accepter_role)
    collect_donation(client, donation_id, accepter_token)
    return donation_id, donor_token, accepter_token


def set_available_until_in_past(db: Session, donation_id: str) -> None:
    donation = db.get(Donation, donation_id)
    donation.available_until = datetime.now(timezone.utc) - timedelta(hours=1)
    db.add(donation)
    db.commit()


def set_status(db: Session, donation_id: str, status: str) -> None:
    donation = db.get(Donation, donation_id)
    donation.status = status
    db.add(donation)
    db.commit()


def test_ngo_can_mark_accepted_donation_collected(client: TestClient) -> None:
    donation_id, _, ngo_token = create_accepted_donation(client, "NGO")

    response = collect_donation(client, donation_id, ngo_token)

    assert response.status_code == 200
    assert response.json()["status"] == "COLLECTED"


def test_volunteer_can_mark_accepted_donation_collected(client: TestClient) -> None:
    donation_id, _, volunteer_token = create_accepted_donation(client, "VOLUNTEER")

    response = collect_donation(client, donation_id, volunteer_token)

    assert response.status_code == 200
    assert response.json()["status"] == "COLLECTED"


def test_collected_at_is_stored(client: TestClient) -> None:
    donation_id, _, ngo_token = create_accepted_donation(client, "NGO")

    response = collect_donation(client, donation_id, ngo_token)

    assert response.status_code == 200
    assert response.json()["collected_at"] is not None


def test_status_changes_accepted_to_collected(client: TestClient) -> None:
    donation_id, _, ngo_token = create_accepted_donation(client, "NGO")

    response = collect_donation(client, donation_id, ngo_token)

    assert response.json()["status"] == "COLLECTED"


def test_donor_cannot_mark_donation_collected(client: TestClient) -> None:
    donation_id, donor_token, _ = create_accepted_donation(client, "NGO")

    response = collect_donation(client, donation_id, donor_token)

    assert response.status_code == 403


def test_different_ngo_cannot_mark_another_ngos_donation_collected(client: TestClient) -> None:
    donation_id, _, _ = create_accepted_donation(client, "NGO")
    other_ngo_token = register_and_login(client, "other-ngo@example.com", "NGO")

    response = collect_donation(client, donation_id, other_ngo_token)

    assert response.status_code == 403


def test_cannot_collect_available_donation(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]

    response = collect_donation(client, donation_id, ngo_token)

    assert response.status_code == 409


def test_cannot_collect_cancelled_donation(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]
    client.post(f"/donations/{donation_id}/cancel", headers=auth_header(donor_token))

    response = collect_donation(client, donation_id, ngo_token)

    assert response.status_code == 409


def test_cannot_collect_distributed_donation(client: TestClient) -> None:
    donation_id, _, ngo_token = create_collected_donation(client, "NGO")
    distribute_donation(client, donation_id, ngo_token)

    response = collect_donation(client, donation_id, ngo_token)

    assert response.status_code == 409


def test_ngo_can_mark_collected_donation_distributed(client: TestClient) -> None:
    donation_id, _, ngo_token = create_collected_donation(client, "NGO")

    response = distribute_donation(client, donation_id, ngo_token)

    assert response.status_code == 200
    assert response.json()["status"] == "DISTRIBUTED"


def test_volunteer_can_mark_collected_donation_distributed(client: TestClient) -> None:
    donation_id, _, volunteer_token = create_collected_donation(client, "VOLUNTEER")

    response = distribute_donation(client, donation_id, volunteer_token)

    assert response.status_code == 200
    assert response.json()["status"] == "DISTRIBUTED"


def test_distributed_at_is_stored(client: TestClient) -> None:
    donation_id, _, ngo_token = create_collected_donation(client, "NGO")

    response = distribute_donation(client, donation_id, ngo_token)

    assert response.status_code == 200
    assert response.json()["distributed_at"] is not None


def test_status_changes_collected_to_distributed(client: TestClient) -> None:
    donation_id, _, ngo_token = create_collected_donation(client, "NGO")

    response = distribute_donation(client, donation_id, ngo_token)

    assert response.json()["status"] == "DISTRIBUTED"


def test_donor_cannot_mark_distributed(client: TestClient) -> None:
    donation_id, donor_token, _ = create_collected_donation(client, "NGO")

    response = distribute_donation(client, donation_id, donor_token)

    assert response.status_code == 403


def test_different_ngo_cannot_mark_another_ngos_donation_distributed(client: TestClient) -> None:
    donation_id, _, ngo_token = create_collected_donation(client, "NGO")
    other_ngo_token = register_and_login(client, "other-ngo@example.com", "NGO")

    response = distribute_donation(client, donation_id, other_ngo_token)

    assert response.status_code == 403


def test_cannot_distribute_accepted_donation_directly(client: TestClient) -> None:
    donation_id, _, ngo_token = create_accepted_donation(client, "NGO")

    response = distribute_donation(client, donation_id, ngo_token)

    assert response.status_code == 409


def test_cannot_distribute_available_donation(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]

    response = distribute_donation(client, donation_id, ngo_token)

    assert response.status_code == 409


def test_donor_sees_accepted_status(client: TestClient) -> None:
    donation_id, donor_token, _ = create_accepted_donation(client, "NGO")

    response = client.get(f"/donations/{donation_id}", headers=auth_header(donor_token))

    assert response.status_code == 200
    assert response.json()["status"] == "ACCEPTED"


def test_donor_sees_collected_status(client: TestClient) -> None:
    donation_id, donor_token, _ = create_collected_donation(client, "NGO")

    response = client.get(f"/donations/{donation_id}", headers=auth_header(donor_token))

    assert response.status_code == 200
    assert response.json()["status"] == "COLLECTED"
    assert response.json()["collected_at"] is not None


def test_donor_sees_distributed_status(client: TestClient) -> None:
    donation_id, donor_token, ngo_token = create_collected_donation(client, "NGO")
    distribute_donation(client, donation_id, ngo_token)

    response = client.get(f"/donations/{donation_id}", headers=auth_header(donor_token))

    assert response.status_code == 200
    assert response.json()["status"] == "DISTRIBUTED"
    assert response.json()["distributed_at"] is not None


def test_accepted_at_is_preserved_after_collection_and_distribution(client: TestClient) -> None:
    donation_id, _, ngo_token = create_accepted_donation(client, "NGO")
    accepted_at = client.get(f"/donations/{donation_id}", headers=auth_header(ngo_token)).json()["accepted_at"]

    collect_donation(client, donation_id, ngo_token)
    distribute_donation(client, donation_id, ngo_token)
    response = client.get(f"/donations/{donation_id}", headers=auth_header(ngo_token))

    assert response.json()["accepted_at"] == accepted_at


def test_collected_at_is_preserved_after_distribution(client: TestClient) -> None:
    donation_id, _, ngo_token = create_collected_donation(client, "NGO")
    collected_at = client.get(f"/donations/{donation_id}", headers=auth_header(ngo_token)).json()["collected_at"]

    distribute_donation(client, donation_id, ngo_token)
    response = client.get(f"/donations/{donation_id}", headers=auth_header(ngo_token))

    assert response.json()["collected_at"] == collected_at


def test_completed_donation_remains_accessible_in_history(client: TestClient) -> None:
    donation_id, _, ngo_token = create_collected_donation(client, "NGO")
    distribute_donation(client, donation_id, ngo_token)

    response = client.get("/donations/accepted/my?status=DISTRIBUTED", headers=auth_header(ngo_token))

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == donation_id
    assert response.json()[0]["status"] == "DISTRIBUTED"


def test_donor_cannot_cancel_accepted_donation(client: TestClient) -> None:
    donation_id, donor_token, _ = create_accepted_donation(client, "NGO")

    response = client.post(f"/donations/{donation_id}/cancel", headers=auth_header(donor_token))

    assert response.status_code == 409


def test_accepted_donation_is_not_auto_expired_after_deadline(
    client: TestClient,
    db_session: Session,
) -> None:
    donation_id, donor_token, _ = create_accepted_donation(client, "NGO")
    set_available_until_in_past(db_session, donation_id)

    response = client.get(f"/donations/{donation_id}", headers=auth_header(donor_token))

    assert response.status_code == 200
    assert response.json()["status"] == "ACCEPTED"


def test_repeated_collection_attempts_allow_only_one_success(client: TestClient) -> None:
    donation_id, _, ngo_token = create_accepted_donation(client, "NGO")

    first_response = collect_donation(client, donation_id, ngo_token)
    second_response = collect_donation(client, donation_id, ngo_token)

    assert sorted([first_response.status_code, second_response.status_code]) == [200, 409]


def test_repeated_distribution_attempts_allow_only_one_success(client: TestClient) -> None:
    donation_id, _, ngo_token = create_collected_donation(client, "NGO")

    first_response = distribute_donation(client, donation_id, ngo_token)
    second_response = distribute_donation(client, donation_id, ngo_token)

    assert sorted([first_response.status_code, second_response.status_code]) == [200, 409]


def test_cannot_collect_missing_donation(client: TestClient) -> None:
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")

    response = collect_donation(client, "missing-id", ngo_token)

    assert response.status_code == 404


def test_cannot_distribute_missing_donation(client: TestClient) -> None:
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")

    response = distribute_donation(client, "missing-id", ngo_token)

    assert response.status_code == 404
