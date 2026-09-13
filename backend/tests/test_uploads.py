from pathlib import Path

from fastapi.testclient import TestClient

from tests.test_donations import auth_header, register_and_login


def test_donor_can_upload_donation_image(client: TestClient) -> None:
    token = register_and_login(client, "donor@example.com", "DONOR")

    response = client.post(
        "/uploads/donation-image",
        files={"image": ("food.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        headers=auth_header(token),
    )

    assert response.status_code == 200
    image_url = response.json()["image_url"]
    assert image_url.startswith("/uploads/donations/")

    file_path = Path("uploads") / "donations" / Path(image_url).name
    if file_path.exists():
        file_path.unlink()


def test_upload_rejects_non_image_file(client: TestClient) -> None:
    token = register_and_login(client, "donor@example.com", "DONOR")

    response = client.post(
        "/uploads/donation-image",
        files={"image": ("notes.txt", b"not an image", "text/plain")},
        headers=auth_header(token),
    )

    assert response.status_code == 400
