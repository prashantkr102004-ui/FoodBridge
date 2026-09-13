# FoodBridge Backend

FastAPI backend for FoodBridge. The main project guide is in `../README.md`.

## Setup

```powershell
cd "C:\Users\PK\Documents\CODING\food bridge\FoodBridge\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

For the local setup in this workspace, `backend\.env` currently uses SQLite:

```env
DATABASE_URL=sqlite:///./foodbridge_local.db
```

For PostgreSQL, use:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/foodbridge
```

## Commands

Run migrations:

```powershell
alembic upgrade head
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Open Swagger:

```text
http://127.0.0.1:8000/docs
```

Health checks:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/health
```

## Notes

- Public registration allows `DONOR`, `NGO`, and `VOLUNTEER`.
- Public registration does not allow `ADMIN`.
- Donation photos are uploaded through `/uploads/donation-image`.
- Uploaded local files are stored under `backend/uploads/` and ignored by Git.
- Production deployment notes are in the root README.
