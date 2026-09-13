from fastapi.testclient import TestClient

from tests.test_donations import auth_header, create_donation, create_test_admin, register_and_login
from tests.test_donation_lifecycle import accept_donation, collect_donation, distribute_donation


def register_user_and_get_id(client: TestClient, email: str, role: str) -> str:
    if role == "ADMIN":
        create_test_admin(email)
        token = client.post(
            "/auth/login",
            json={"email": email, "password": "strongpass123"},
        ).json()["access_token"]
        return client.get("/auth/me", headers=auth_header(token)).json()["id"]
    register_response = client.post(
        "/auth/register",
        json={
            "name": f"{role.title()} Person",
            "email": email,
            "phone": "9876543210",
            "password": "strongpass123",
            "role": role,
            "organization_name": f"{role.title()} Org",
            "location": "Pune",
        },
    )
    return register_response.json()["id"]


def setup_lifecycle_donation(client: TestClient, donor_token: str, receiver_token: str) -> str:
    donation_id = create_donation(client, donor_token).json()["id"]
    accept_donation(client, donation_id, receiver_token)
    collect_donation(client, donation_id, receiver_token)
    distribute_donation(client, donation_id, receiver_token)
    return donation_id


def test_donor_dashboard_returns_total_count(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    create_donation(client, donor_token)
    create_donation(client, donor_token, food_name="Rice Packets")

    response = client.get("/dashboard/donor", headers=auth_header(donor_token))

    assert response.status_code == 200
    assert response.json()["total_donations"] == 2


def test_donor_dashboard_status_counts_are_correct(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    available_id = create_donation(client, donor_token).json()["id"]
    accepted_id = create_donation(client, donor_token, food_name="Accepted Rice").json()["id"]
    cancelled_id = create_donation(client, donor_token, food_name="Cancelled Rice").json()["id"]
    accept_donation(client, accepted_id, ngo_token)
    client.post(f"/donations/{cancelled_id}/cancel", headers=auth_header(donor_token))

    response = client.get("/dashboard/donor", headers=auth_header(donor_token))
    data = response.json()

    assert response.status_code == 200
    assert data["available_donations"] == 1
    assert data["accepted_donations"] == 1
    assert data["cancelled_donations"] == 1


def test_donor_dashboard_recent_donations_are_limited(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    for index in range(6):
        create_donation(client, donor_token, food_name=f"Food {index}")

    response = client.get("/dashboard/donor", headers=auth_header(donor_token))

    assert response.status_code == 200
    assert len(response.json()["recent_donations"]) == 5


def test_donor_dashboard_only_shows_own_statistics(client: TestClient) -> None:
    donor_a_token = register_and_login(client, "donor-a@example.com", "DONOR")
    donor_b_token = register_and_login(client, "donor-b@example.com", "DONOR")
    create_donation(client, donor_a_token)
    create_donation(client, donor_b_token)
    create_donation(client, donor_b_token, food_name="Other Food")

    response = client.get("/dashboard/donor", headers=auth_header(donor_a_token))

    assert response.status_code == 200
    assert response.json()["total_donations"] == 1


def test_donor_dashboard_quantity_totals_are_grouped_by_unit(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    create_donation(client, donor_token)

    response = client.get("/dashboard/donor", headers=auth_header(donor_token))

    assert response.status_code == 200
    assert response.json()["total_quantity_donated"] == {"MEALS": 25.0}


def test_receiver_dashboard_counts_are_correct(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    accepted_id = create_donation(client, donor_token).json()["id"]
    collected_id = create_donation(client, donor_token, food_name="Collected Food").json()["id"]
    distributed_id = create_donation(client, donor_token, food_name="Distributed Food").json()["id"]
    accept_donation(client, accepted_id, ngo_token)
    accept_donation(client, collected_id, ngo_token)
    collect_donation(client, collected_id, ngo_token)
    accept_donation(client, distributed_id, ngo_token)
    collect_donation(client, distributed_id, ngo_token)
    distribute_donation(client, distributed_id, ngo_token)

    response = client.get("/dashboard/receiver", headers=auth_header(ngo_token))
    data = response.json()

    assert response.status_code == 200
    assert data["accepted_count"] == 1
    assert data["collected_count"] == 1
    assert data["distributed_count"] == 1


def test_receiver_dashboard_is_scoped_to_current_user(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_a_token = register_and_login(client, "ngo-a@example.com", "NGO")
    ngo_b_token = register_and_login(client, "ngo-b@example.com", "NGO")
    donation_id = create_donation(client, donor_token).json()["id"]
    accept_donation(client, donation_id, ngo_b_token)

    response = client.get("/dashboard/receiver", headers=auth_header(ngo_a_token))

    assert response.status_code == 200
    assert response.json()["accepted_count"] == 0


def test_receiver_dashboard_available_count_and_rescued_quantity(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    create_donation(client, donor_token)
    setup_lifecycle_donation(client, donor_token, ngo_token)

    response = client.get("/dashboard/receiver", headers=auth_header(ngo_token))
    data = response.json()

    assert response.status_code == 200
    assert data["available_donations_count"] == 1
    assert data["total_rescued_quantity"] == {"MEALS": 25.0}


def test_dashboard_authorization_rules(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    volunteer_token = register_and_login(client, "volunteer@example.com", "VOLUNTEER")

    assert client.get("/dashboard/donor", headers=auth_header(donor_token)).status_code == 200
    assert client.get("/dashboard/receiver", headers=auth_header(ngo_token)).status_code == 200
    assert client.get("/dashboard/receiver", headers=auth_header(volunteer_token)).status_code == 200
    assert client.get("/dashboard/receiver", headers=auth_header(donor_token)).status_code == 403
    assert client.get("/dashboard/donor", headers=auth_header(ngo_token)).status_code == 403
    assert client.get("/dashboard/donor").status_code == 401


def test_admin_dashboard_counts_are_correct(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    register_and_login(client, "ngo@example.com", "NGO")
    register_and_login(client, "volunteer@example.com", "VOLUNTEER")
    create_donation(client, donor_token)

    response = client.get("/admin/dashboard", headers=auth_header(admin_token))
    data = response.json()

    assert response.status_code == 200
    assert data["total_users"] == 4
    assert data["total_donors"] == 1
    assert data["total_ngos"] == 1
    assert data["total_volunteers"] == 1
    assert data["total_admins"] == 1
    assert data["available_donations"] == 1


def test_admin_dashboard_rescued_quantity_counts_distributed_only(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    ngo_token = register_and_login(client, "ngo@example.com", "NGO")
    setup_lifecycle_donation(client, donor_token, ngo_token)

    response = client.get("/admin/dashboard", headers=auth_header(admin_token))

    assert response.status_code == 200
    assert response.json()["quantity_rescued_by_unit"] == {"MEALS": 25.0}


def test_non_admin_cannot_access_admin_dashboard(client: TestClient) -> None:
    donor_token = register_and_login(client, "donor@example.com", "DONOR")

    assert client.get("/admin/dashboard", headers=auth_header(donor_token)).status_code == 403
    assert client.get("/admin/dashboard").status_code == 401


def test_admin_user_list_filters_search_and_pagination(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    register_and_login(client, "donor@example.com", "DONOR")
    register_and_login(client, "ngo-special@example.com", "NGO")

    list_response = client.get("/admin/users", headers=auth_header(admin_token))
    role_response = client.get("/admin/users?role=NGO", headers=auth_header(admin_token))
    search_response = client.get("/admin/users?search=special", headers=auth_header(admin_token))
    page_response = client.get("/admin/users?page=1&page_size=2", headers=auth_header(admin_token))

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 3
    assert role_response.json()["total"] == 1
    assert role_response.json()["items"][0]["role"] == "NGO"
    assert search_response.json()["total"] == 1
    assert page_response.json()["page_size"] == 2
    assert len(page_response.json()["items"]) == 2
    assert "password_hash" not in page_response.text


def test_admin_user_details_and_missing_user(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    donor_id = register_user_and_get_id(client, "donor@example.com", "DONOR")

    response = client.get(f"/admin/users/{donor_id}", headers=auth_header(admin_token))
    missing_response = client.get("/admin/users/missing-id", headers=auth_header(admin_token))

    assert response.status_code == 200
    assert response.json()["id"] == donor_id
    assert response.json()["donations_created"] == 0
    assert missing_response.status_code == 404


def test_admin_donation_list_filters_and_details(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    donor_token = register_and_login(client, "donor@example.com", "DONOR")
    donation_id = create_donation(client, donor_token).json()["id"]

    list_response = client.get("/admin/donations", headers=auth_header(admin_token))
    status_response = client.get("/admin/donations?status=AVAILABLE", headers=auth_header(admin_token))
    detail_response = client.get(f"/admin/donations/{donation_id}", headers=auth_header(admin_token))
    missing_response = client.get("/admin/donations/missing-id", headers=auth_header(admin_token))

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert status_response.json()["total"] == 1
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == donation_id
    assert detail_response.json()["donor_phone"] == "9876543210"
    assert missing_response.status_code == 404


def test_admin_can_deactivate_and_reactivate_user(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    donor_id = register_user_and_get_id(client, "donor@example.com", "DONOR")

    deactivate_response = client.post(
        f"/admin/users/{donor_id}/deactivate",
        headers=auth_header(admin_token),
    )
    activate_response = client.post(
        f"/admin/users/{donor_id}/activate",
        headers=auth_header(admin_token),
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False
    assert activate_response.status_code == 200
    assert activate_response.json()["is_active"] is True


def test_admin_cannot_deactivate_self(client: TestClient) -> None:
    admin_id = register_user_and_get_id(client, "admin@example.com", "ADMIN")
    admin_token = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "strongpass123"},
    ).json()["access_token"]

    response = client.post(f"/admin/users/{admin_id}/deactivate", headers=auth_header(admin_token))

    assert response.status_code == 400


def test_deactivated_user_cannot_login_or_use_old_jwt(client: TestClient) -> None:
    admin_token = register_and_login(client, "admin@example.com", "ADMIN")
    donor_id = register_user_and_get_id(client, "donor@example.com", "DONOR")
    donor_login = client.post(
        "/auth/login",
        json={"email": "donor@example.com", "password": "strongpass123"},
    )
    donor_token = donor_login.json()["access_token"]

    client.post(f"/admin/users/{donor_id}/deactivate", headers=auth_header(admin_token))
    login_response = client.post(
        "/auth/login",
        json={"email": "donor@example.com", "password": "strongpass123"},
    )
    protected_response = client.get("/auth/me", headers=auth_header(donor_token))
    client.post(f"/admin/users/{donor_id}/activate", headers=auth_header(admin_token))
    reactivated_login = client.post(
        "/auth/login",
        json={"email": "donor@example.com", "password": "strongpass123"},
    )

    assert donor_login.status_code == 200
    assert login_response.status_code == 403
    assert protected_response.status_code == 403
    assert reactivated_login.status_code == 200
