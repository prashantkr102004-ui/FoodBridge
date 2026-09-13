# FoodBridge Security Notes

FoodBridge is a college-project full-stack application. This document explains the security controls currently implemented and the limits that should be improved before a real public production launch.

## Implemented Controls

- **Password hashing:** User passwords are hashed with `passlib` and bcrypt. Plain-text passwords are accepted only during registration/login requests and are never returned by API responses.
- **JWT authentication:** The backend signs access tokens with `SECRET_KEY` from environment configuration. Tokens include expiration and are rejected when expired, malformed, or tied to a missing/deactivated user.
- **Environment secrets:** `DATABASE_URL`, `SECRET_KEY`, JWT settings, and CORS origins are read from environment variables. Real `.env` files are ignored by Git; `.env.example` contains placeholders only.
- **Public registration limits:** Public registration allows `DONOR`, `NGO`, and `VOLUNTEER`. `ADMIN` accounts are blocked from public registration and must be created/promoted by a trusted database/admin setup step.
- **Role authorization:** Protected APIs use backend role dependencies. Frontend route guards are only a user-experience layer; the backend remains the authority.
- **Object ownership:** Donors can modify only their own donations. Receivers can operate only on donations they accepted. Notification, analytics, and profile APIs derive the user from the JWT instead of trusting client-supplied user IDs.
- **Donation lifecycle safety:** Status changes are handled through service functions and dedicated endpoints. Generic PATCH requests cannot set arbitrary statuses.
- **Concurrency protection:** Accept, collect, and distribute operations use conditional database updates so only one request can move a donation from the expected current state.
- **Input validation:** Pydantic schemas validate emails, roles, enums, quantities, timestamps, coordinates, pagination/filter values, and practical string lengths.
- **Location privacy:** User coordinates are used for nearby matching. The app does not store movement history, background GPS tracking, or continuous location updates.
- **Notification privacy:** Users can list, count, and mark read only their own notifications.
- **Analytics authorization:** Donor and receiver analytics are scoped to the authenticated user. Admin analytics and CSV export require `ADMIN`.
- **CSV export protection:** Admin CSV export excludes passwords, tokens, secrets, and other security data. Formula-like text values are prefixed before export to reduce spreadsheet formula-injection risk.
- **CORS configuration:** Allowed frontend origins are configured through `BACKEND_CORS_ORIGINS`.

## Known Production Improvements

These are intentionally not implemented in Phase 11:

- Rate limiting for login and registration.
- HttpOnly secure-cookie auth as an alternative to browser local storage.
- Password reset and email verification.
- Stronger admin bootstrap tooling.
- Centralized production logging and monitoring.
- Detailed audit logs for admin and lifecycle actions.
- Security headers from a production reverse proxy.
- Dependency vulnerability management policy and scheduled updates.
- Backup, restore, and disaster-recovery procedures.
