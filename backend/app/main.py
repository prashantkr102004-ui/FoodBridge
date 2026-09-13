from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes import admin, analytics, auth, dashboard, donations, health, notifications, recommendations, uploads, users


settings = get_settings()
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(donations.router)
app.include_router(recommendations.router)
app.include_router(uploads.router)
app.include_router(notifications.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
