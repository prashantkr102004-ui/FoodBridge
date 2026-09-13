from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.models.user import User, UserRole
from app.utils.dependencies import require_roles

router = APIRouter(prefix="/uploads", tags=["Uploads"])

UPLOADS_BASE = Path(__file__).resolve().parents[2] / "uploads"
DONATION_UPLOAD_ROOT = UPLOADS_BASE / "donations"
RECEIVER_UPLOAD_ROOT = UPLOADS_BASE / "receivers"
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_BYTES = 3 * 1024 * 1024


async def save_image_upload(image: UploadFile, upload_root: Path, public_prefix: str) -> dict[str, str]:
    extension = ALLOWED_IMAGE_TYPES.get(image.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG, or WEBP images are allowed",
        )

    contents = await image.read()
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size must be 3 MB or less",
        )

    upload_root.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    file_path = upload_root / filename
    file_path.write_bytes(contents)

    return {"image_url": f"{public_prefix}/{filename}"}


@router.post("/donation-image")
async def upload_donation_image(
    image: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.DONOR)),
) -> dict[str, str]:
    return await save_image_upload(image, DONATION_UPLOAD_ROOT, "/uploads/donations")


@router.post("/receiver-image")
async def upload_receiver_image(image: UploadFile = File(...)) -> dict[str, str]:
    return await save_image_upload(image, RECEIVER_UPLOAD_ROOT, "/uploads/receivers")
