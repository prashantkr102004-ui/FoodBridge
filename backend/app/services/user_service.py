from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserLocationUpdate, UserRegister
from app.utils.security import hash_password


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email.lower())
    return db.scalar(statement)


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, user_in: UserRegister) -> User:
    user = User(
        name=user_in.name,
        email=user_in.email.lower(),
        phone=user_in.phone,
        password_hash=hash_password(user_in.password),
        role=user_in.role.value,
        organization_name=user_in.organization_name,
        receiver_type=user_in.receiver_type,
        receiver_focus=user_in.receiver_focus,
        profile_image_url=user_in.profile_image_url,
        location=user_in.location,
        latitude=user_in.latitude,
        longitude=user_in.longitude,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_location(db: Session, user: User, location_in: UserLocationUpdate) -> User:
    update_data = location_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
