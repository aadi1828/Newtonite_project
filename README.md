# Newtonite Operations

An internal operations-work management MVP for coordinating incidents, customer issues, payments, compliance requests, and operational tasks.

## Features
- React + Vite dashboard with search, filters, priority/status indicators, and work-item details.
- FastAPI REST API with JWT login and seeded demo users.
- PostgreSQL via Docker Compose (SQLite fallback for quick local development).
- Team-scoped authorization, workflow validation, atomic claim, optimistic concurrency (`version`), comments, and transactional activity history.
- Pytest tests for key API behaviours.

## Quick start (Docker)
1. Copy `.env.example` to `.env`.
2. Run `docker compose up --build`.
3. API docs: http://localhost:8000/docs
4. Frontend: http://localhost:5173

If Docker is unavailable, run the backend locally with SQLite:
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL="sqlite:///./newtonite.db"
py -m app.seed
uvicorn app.main:app --reload
```
In a second terminal:
```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

## Demo accounts
Password for all seeded accounts: `NewtoniteDemo!2026`

- `admin@newtonite.local` — Admin
- `lead@newtonite.local` — Lead
- `member@newtonite.local` — Member
- `viewer@newtonite.local` — Viewer
- `outsider@newtonite.local` — member of a separate team, useful for authorization demos

These are local demo credentials only. Change them before any public deployment.

## Tests
```powershell
cd backend
py -m pip install -r requirements.txt
py -m pytest -q
```

## Notes
- JWT secret is configured by `SECRET_KEY`; use a unique strong value outside local demos.
- This is an assessment MVP, not a production-ready enterprise service.
- The frontend keeps the access token in session storage for the demo. For production, prefer secure, HttpOnly cookies and CSRF protection.
- The MVP implements core correctness behaviours; it does not include email delivery, file attachments, SSO, WebSockets, or a distributed background worker.
