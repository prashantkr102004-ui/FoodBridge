from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
def root() -> dict[str, str]:
    return {"message": "FoodBridge API is running"}


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
