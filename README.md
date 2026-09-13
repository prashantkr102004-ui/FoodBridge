# FoodBridge

FoodBridge is a full-stack surplus food donation and distribution platform. It connects donors such as restaurants, college canteens, hotels, and event organizers with NGOs and volunteers who can collect and distribute edible surplus food.

## Tech Stack

- Frontend: React, Vite, React Router, Axios, Leaflet
- Backend: Python, FastAPI, SQLAlchemy, Alembic
- Database: PostgreSQL
- Authentication: JWT with role-based authorization

## User Roles

- `DONOR`: creates and manages food donations.
- `NGO`: finds, accepts, collects, and distributes food.
- `VOLUNTEER`: works like an NGO receiver for pickup and distribution.
- `ADMIN`: manages users, views platform data, analytics, and CSV reports.

Public registration allows only `DONOR`, `NGO`, and `VOLUNTEER`. Admin accounts must be created or promoted by a trusted database/admin setup step.

## Main Features

- User registration and login
- Secure password hashing
- JWT authentication
- Active/inactive account handling
- Donation lifecycle: `AVAILABLE -> ACCEPTED -> COLLECTED -> DISTRIBUTED`
- Terminal donation states: `CANCELLED`, `EXPIRED`
- Donation creation, editing, cancellation, and expiry handling
- Donation photo upload from device or camera
- NGO/Volunteer acceptance with double-acceptance protection
- Collection and distribution tracking
- In-app notifications
- User and pickup coordinates
- Nearby food search using Haversine distance
- Map display with OpenStreetMap/Leaflet
- Rule-based smart recommendations
- Donor, receiver, and admin dashboards
- Impact analytics
- Admin CSV export
- Security hardening and automated tests
- Production-ready deployment configuration

## Project Structure

```text
FoodBridge/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   ├── .env.example
│   ├── alembic.ini
│   ├── README.md
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── context/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── .env.example
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json
├── .gitignore
├── README.md
├── SECURITY.md
└── render.yaml
```

## Backend Setup on Windows

Open PowerShell:

```powershell
cd "C:\Users\PK\Documents\CODING\food bridge\FoodBridge\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

If PowerShell blocks virtual environment activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Create the PostgreSQL database:

```sql
CREATE DATABASE foodbridge;
```

Edit `backend\.env`:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/foodbridge
SECRET_KEY=replace-this-with-a-long-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000
```

Run migrations:

```powershell
alembic upgrade head
```

Start the backend:

```powershell
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Health checks:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/health
```

## Frontend Setup on Windows

Open a second PowerShell window:

```powershell
cd "C:\Users\PK\Documents\CODING\food bridge\FoodBridge\frontend"
npm install
copy .env.example .env
npm run dev
```

Edit `frontend\.env` if needed:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Open the frontend:

```text
http://localhost:5173
```

## Testing

Backend tests:

```powershell
cd "C:\Users\PK\Documents\CODING\food bridge\FoodBridge\backend"
.\.venv\Scripts\python.exe -m pytest
```

Frontend tests:

```powershell
cd "C:\Users\PK\Documents\CODING\food bridge\FoodBridge\frontend"
npm test
```

Frontend production build:

```powershell
npm run build
```

Frontend dependency audit:

```powershell
npm audit
```

## Important API Groups

- Authentication: `/auth/register`, `/auth/login`, `/auth/me`
- User location: `/users/me/location`
- Donations: `/donations`, `/donations/my`, `/donations/{id}`
- Uploads: `/uploads/donation-image`
- Lifecycle: `/donations/{id}/accept`, `/collect`, `/distribute`, `/cancel`
- Nearby food: `/donations/nearby`
- Recommendations: `/recommendations/donations`
- Notifications: `/notifications`
- Dashboards: `/dashboard/donor`, `/dashboard/receiver`
- Admin: `/admin/dashboard`, `/admin/users`, `/admin/donations`
- Analytics: `/analytics/donor`, `/analytics/receiver`, `/analytics/admin`
- CSV export: `/analytics/admin/export.csv`

## Frontend Routes

- Public: `/`, `/login`, `/register`
- Shared authenticated: `/profile`, `/notifications`
- Donor: `/donor`, `/donor/post`, `/donor/donations`, `/donor/impact`
- Receiver: `/receiver`, `/receiver/available`, `/receiver/recommendations`, `/receiver/accepted`, `/receiver/impact`
- Admin: `/admin`, `/admin/users`, `/admin/donations`, `/admin/analytics`

## Manual Test Flow

1. Register and login as a `DONOR`.
2. Create a food donation with pickup address and an optional food picture.
3. Register and login as an `NGO` or `VOLUNTEER`.
4. Set receiver location in Profile.
5. Open Available Food, Nearby Food, and Smart Recommendations.
6. Accept the donation.
7. Login again as the donor and check the notification.
8. Login as the receiver and mark the donation collected.
9. Mark the donation distributed.
10. Login as donor and confirm lifecycle notifications and impact analytics.
11. Login as admin and check users, donations, analytics, and CSV export.

## Analytics Rules

- Only `DISTRIBUTED` donations count as successfully rescued/completed food.
- Quantity totals are grouped by unit. `KG`, `MEALS`, `PACKETS`, and `OTHER` are never added together.
- Donor/admin success rate:

```text
distributed / (distributed + cancelled + expired) * 100
```

- Receiver completion rate:

```text
distributed by this receiver / total accepted by this receiver * 100
```

## Smart Recommendation Formula

FoodBridge uses a transparent rule-based score, not deep learning:

```text
final_score =
  distance_score * 0.40
  + urgency_score * 0.30
  + quantity_score * 0.15
  + preference_score * 0.15
```

- Distance uses Haversine straight-line kilometers.
- Urgency gives more weight to food expiring sooner.
- Quantity is scored within its own unit type.
- Preference uses receiver history only when enough history exists.
- New receivers get a neutral preference score.

## Deployment

Recommended simple deployment:

- Backend: Render Web Service
- Database: Render PostgreSQL
- Frontend: Vercel

Backend deployment file:

```text
render.yaml
```

Backend build command:

```text
cd backend && pip install -r requirements.txt
```

Backend start command:

```text
cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Backend production environment variables:

```env
DATABASE_URL=postgresql://your-hosted-postgres-url
SECRET_KEY=your-long-random-production-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
BACKEND_CORS_ORIGINS=https://your-vercel-app.vercel.app
```

The backend supports both `postgres://...` and `postgresql://...` hosted database URLs.

Generate a strong secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Frontend deployment file:

```text
frontend/vercel.json
```

Vercel settings:

```text
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
```

Frontend production environment variable:

```env
VITE_API_BASE_URL=https://your-render-backend.onrender.com
```

Use HTTPS URLs in production and set `BACKEND_CORS_ORIGINS` to the exact deployed frontend URL.

## Admin Account Setup

Public registration blocks `ADMIN`. For local demo setup:

1. Register a normal trusted user.
2. Promote that user in PostgreSQL:

```sql
UPDATE users SET role = 'ADMIN' WHERE email = 'admin@example.com';
```

## Security Notes

See `SECURITY.md` for security details. In short:

- Passwords are hashed.
- JWT secrets come from environment variables.
- Protected routes are enforced by the backend.
- Users cannot access other users' private notifications or analytics.
- Donation workflow transitions are controlled by service logic.
- CSV export avoids password/token fields and sanitizes formula-like values.
- Browser geolocation is permission-based and not continuous tracking.

## Scope Not Included

FoodBridge does not include payment, QR/OTP, SMS/WhatsApp, email notifications, WebSockets, live GPS tracking, ratings, image recognition, demand prediction, or deep-learning AI.
