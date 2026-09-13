from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserLocationUpdate, UserResponse
from app.services.user_service import update_user_location
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.patch("/me/location", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_my_location(
    location_in: UserLocationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    return update_user_location(db, current_user, location_in)
