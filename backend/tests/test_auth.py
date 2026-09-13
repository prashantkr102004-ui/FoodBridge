from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from jose import jwt

from app.config import get_settings


def valid_registration_payload(email: str = "donor@example.com") -> dict[str, str]:
    return {
        "name": "Test Donor",
        "email": email,
        "phone": "9876543210",
        "password": "strongpass123",
        "role": "DONOR",
        "organization_name": "Campus Canteen",
        "location": "Pune",
    }


def register_user(client: TestClient, email: str = "donor@example.com"):
    return client.post("/auth/register", json=valid_registration_payload(email))


def login_user(client: TestClient, email: str = "donor@example.com", password: str = "strongpass123"):
    return client.post("/auth/login", json={"email": email, "password": password})


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "FoodBridge API is running"}


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_successful_registration(client: TestClient) -> None:
    response = register_user(client)
    data = response.json()

    assert response.status_code == 201
    assert data["email"] == "donor@example.com"
    assert data["role"] == "DONOR"
    assert "password_hash" not in data
    assert "password" not in data


def test_duplicate_email_registration_is_rejected(client: TestClient) -> None:
    register_user(client)
    response = register_user(client)

    assert response.status_code == 409
    assert response.json()["detail"] == "An account with this email already exists"


def test_successful_login(client: TestClient) -> None:
    register_user(client)
    response = login_user(client)
    data = response.json()

    assert response.status_code == 200
    assert data["token_type"] == "bearer"
    assert data["access_token"]


def test_wrong_password_login_is_rejected(client: TestClient) -> None:
    register_user(client)
    response = login_user(client, password="wrong-password")

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_unknown_email_login_is_rejected(client: TestClient) -> None:
    response = login_user(client, email="missing@example.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_auth_me_with_valid_token(client: TestClient) -> None:
    register_user(client)
    login_response = login_user(client)
    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    data = response.json()

    assert response.status_code == 200
    assert data["email"] == "donor@example.com"
    assert data["role"] == "DONOR"


def test_auth_me_without_token_is_rejected(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_malformed_jwt_is_rejected(client: TestClient) -> None:
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-valid-token"})

    assert response.status_code == 401


def test_expired_jwt_is_rejected(client: TestClient) -> None:
    register_user(client)
    settings = get_settings()
    token = jwt.encode(
        {"sub": "some-user-id", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_invalid_role_is_rejected(client: TestClient) -> None:
    payload = valid_registration_payload()
    payload["role"] = "RESTAURANT"

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_public_admin_registration_is_blocked(client: TestClient) -> None:
    payload = valid_registration_payload("admin@example.com")
    payload["role"] = "ADMIN"

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 403
    assert response.json()["detail"] == "ADMIN accounts cannot be created through public registration"


def test_invalid_registration_data_is_rejected(client: TestClient) -> None:
    payload = valid_registration_payload()
    payload["password"] = "short"

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
