# FoodBridge

FoodBridge is a full-stack web application built to reduce food waste. The idea is simple: when a restaurant, college canteen, hotel, or event organizer has extra edible food, they can post it on FoodBridge. NGOs and volunteers can then find that food, accept it, collect it, and distribute it to people or groups who need it.

This project was built as a complete college-style software project with authentication, role-based access, donation lifecycle tracking, location-based nearby search, smart recommendations, notifications, analytics, admin controls, tests, and deployment-ready configuration.

## What FoodBridge Does

FoodBridge connects three main sides of the system:

- Donors who post surplus food.
- NGOs and volunteers who accept and distribute food.
- Admins who monitor users, donations, reports, and platform activity.

The main donation flow is:

```text
AVAILABLE -> ACCEPTED -> COLLECTED -> DISTRIBUTED
```

There are also two terminal states:

```text
CANCELLED
EXPIRED
```

Only properly allowed users can move a donation through the workflow. For example, a donor can create and cancel their own available donation, but only the NGO or volunteer who accepted it can mark it collected or distributed.

## Tech Stack

### Frontend

- React
- Vite
- React Router
- Axios
- Leaflet and React-Leaflet for maps

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- JWT authentication

### Database

- PostgreSQL

SQLite is also used locally for easier development/testing in some setups, but PostgreSQL is the main intended database.

## User Roles

### DONOR

Donors can register, login, create food donations, upload or click food photos, track donation status, receive notifications, and view their impact analytics.

### NGO

NGOs can register with organization details, find available food, use nearby search, view smart recommendations, accept donations, collect them, distribute them, and view receiver impact analytics.

### VOLUNTEER

Volunteers work like receiver users. They can accept, collect, and distribute food donations.

### ADMIN

Admins can view platform dashboards, manage users, inspect donations, view analytics, deactivate/reactivate users, and export CSV reports.

Public registration does not allow ADMIN accounts. Admin setup must be done through a trusted database/admin setup step.

## Main Features

- User registration and login
- Public registration for donor, NGO, and volunteer users
- Public ADMIN registration blocked
- Secure password hashing
- JWT-based authentication
- Active/inactive user handling
- Role-based backend authorization
- Donor donation creation and editing
- Donation cancellation and expiry handling
- Food image upload from file or camera
- NGO/accepter profile details and picture upload
- Donation acceptance by NGO/volunteer
- Double-acceptance prevention
- Collection and distribution lifecycle
- In-app notifications
- Notification read/unread state
- User and pickup location support
- Browser geolocation with permission
- Nearby food search using Haversine distance
- OpenStreetMap/Leaflet map display
- Rule-based smart recommendations
- Donor, receiver, and admin dashboards
- Impact analytics
- Admin CSV export
- Security documentation
- Backend and frontend automated tests
- Deployment-ready configuration

## Project Structure

```text
FoodBridge/
├── backend/
│   ├── alembic/
│   │   └── versions/
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

## Local Setup on Windows

The project has two parts, so run the backend and frontend in two separate terminals.

## Backend Setup

Open PowerShell and run:

```powershell
cd "C:\Users\PK\Documents\CODING\food bridge\FoodBridge\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

If PowerShell blocks virtual environment activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Create a PostgreSQL database:

```sql
CREATE DATABASE foodbridge;
```

Open `backend\.env` and set your values:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/foodbridge
SECRET_KEY=replace-this-with-a-long-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000
```

Run database migrations:

```powershell
alembic upgrade head
```

Start the backend:

```powershell
uvicorn app.main:app --reload
```

Open Swagger API docs:

```text
http://127.0.0.1:8000/docs
```

Useful backend check URLs:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/health
```

## Frontend Setup

Open another PowerShell window:

```powershell
cd "C:\Users\PK\Documents\CODING\food bridge\FoodBridge\frontend"
npm install
copy .env.example .env
npm run dev
```

Set the frontend API URL in `frontend\.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Open the React app:

```text
http://localhost:5173
```

## How to Use the App

### Donor Flow

1. Register as a donor.
2. Login.
3. Create a food donation.
4. Add pickup address and food details.
5. Add a picture from device or click a picture using the camera.
6. Track whether the donation is available, accepted, collected, or distributed.
7. Check notifications and donor impact analytics.

### NGO / Accepter Flow

1. Register as NGO/accepter.
2. Enter NGO name, NGO type, address, contact details, and NGO picture.
3. Login as NGO/accepter.
4. Set location if needed.
5. View available food.
6. Use nearby food search.
7. Open smart recommendations.
8. Accept a donation.
9. Mark it collected.
10. Mark it distributed.
11. Check receiver impact analytics.

### Admin Flow

1. Login as admin.
2. View admin dashboard.
3. Manage users.
4. View donations.
5. Check platform analytics.
6. Export CSV impact report.

## Important API Groups

- Authentication: `/auth/register`, `/auth/login`, `/auth/me`
- User profile/location: `/users/me/location`
- Donations: `/donations`, `/donations/my`, `/donations/{id}`
- Uploads: `/uploads/donation-image`, `/uploads/receiver-image`
- Lifecycle: `/donations/{id}/accept`, `/donations/{id}/collect`, `/donations/{id}/distribute`, `/donations/{id}/cancel`
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

## Testing

Run backend tests:

```powershell
cd "C:\Users\PK\Documents\CODING\food bridge\FoodBridge\backend"
.\.venv\Scripts\python.exe -m pytest
```

Run frontend tests:

```powershell
cd "C:\Users\PK\Documents\CODING\food bridge\FoodBridge\frontend"
npm test
```

Build the frontend for production:

```powershell
npm run build
```

Run frontend dependency audit:

```powershell
npm audit
```

## Analytics Rules

FoodBridge does not invent impact numbers. Analytics are calculated from actual donation records.

- A donation counts as successfully rescued/completed only when its status is `DISTRIBUTED`.
- `KG`, `MEALS`, `PACKETS`, and `OTHER` are shown separately.
- The app never adds different units together, because `10 KG + 20 MEALS` is not a meaningful single number.

Donor and admin success rate:

```text
distributed / (distributed + cancelled + expired) * 100
```

Receiver completion rate:

```text
distributed by this receiver / total accepted by this receiver * 100
```

If there is no data yet, the app safely shows zero values instead of `NaN` or broken charts.

## Smart Recommendations

FoodBridge has a rule-based recommendation system. It is not deep learning and it does not call an external AI API.

The final match score is:

```text
final_score =
  distance_score * 0.40
  + urgency_score * 0.30
  + quantity_score * 0.15
  + preference_score * 0.15
```

In simple words:

- Closer donations get a better distance score.
- Donations expiring sooner get a better urgency score.
- Quantity is scored carefully within its own unit.
- Food preference uses receiver history only when enough history exists.
- New receivers are not punished. They get a neutral preference score.

The score is only a ranking score. It is not a scientific probability.

## Location and Maps

FoodBridge uses latitude and longitude for nearby matching.

- Distance is calculated using the Haversine formula.
- This gives approximate straight-line distance in kilometers.
- It is not driving distance.
- Browser geolocation asks for permission.
- The app does not track users continuously.
- Donation maps use OpenStreetMap with Leaflet.

## Notifications

FoodBridge uses in-app notifications only.

Examples:

- Donor is notified when a donation is accepted.
- Donor is notified when food is collected.
- Donor is notified when food is distributed.
- Users can mark notifications as read.

This project does not include email, SMS, WhatsApp, push notifications, or WebSockets.

## Admin Account Setup

Public registration blocks `ADMIN` accounts. For a local demo, create a normal trusted user first and then promote that user in the database:

```sql
UPDATE users SET role = 'ADMIN' WHERE email = 'admin@example.com';
```

This keeps the public registration page safe.

## Deployment Notes

Simple deployment setup:

- Backend: Render Web Service
- Database: Render PostgreSQL
- Frontend: Vercel

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

The backend supports both `postgres://...` and `postgresql://...` database URLs.

Generate a strong secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Frontend deployment settings for Vercel:

```text
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
```

Frontend production environment variable:

```env
VITE_API_BASE_URL=https://your-render-backend.onrender.com
```

Use HTTPS URLs in production. Set `BACKEND_CORS_ORIGINS` to the exact deployed frontend URL.

## Security Summary

More details are in `SECURITY.md`.

Short version:

- Passwords are hashed.
- JWT secrets come from environment variables.
- Backend routes enforce role permissions.
- Users cannot read other users' private notifications or analytics.
- Donation status changes are controlled through workflow endpoints.
- CSV export avoids password/token fields and protects against spreadsheet formula injection.
- Geolocation is permission-based and not continuous tracking.

## Not Included

These items are intentionally outside the current project scope:

- Payments
- QR or OTP pickup verification
- SMS, WhatsApp, or email notifications
- WebSockets
- Live GPS tracking
- Ratings and reviews
- Food image recognition
- Demand prediction
- Deep-learning AI

## Project Status

FoodBridge is technically complete as a full-stack college project. It has a working backend, frontend, database migrations, tests, authentication, role-based workflows, maps, recommendations, notifications, analytics, and deployment-ready setup.
