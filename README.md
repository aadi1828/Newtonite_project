# Newtonite Operations

A full-stack operations management platform designed to help teams manage work items, track progress, and maintain clear accountability. Built as an assessment project, it focuses on practical workflows, team-based permissions, and reliable backend behaviour.

## 🎥 Demo Video

Watch the project walkthrough: [**View Newtonite Operations Demo**](https://drive.google.com/drive/folders/1uSWlog2uXshmKvV7bbXuuJERax5-WJCn)

The video demonstrates the dashboard, work-item management, status updates, comments, and team-based access control.

The walkthrough will cover:

- Dashboard and work-item filters

- Creating and updating work items

- Claiming tasks and changing their status

- Comments and activity history

- Team-based access control

## ✨ Key Features

- **Operations dashboard:** View work items with search, filters, status, and priority indicators.
- **Authentication:** JWT-based login with seeded demo accounts.
- **Team-based access control:** Restrict work-item access according to team membership and role.
- **Work-item lifecycle:** Create tasks, claim items, and manage status transitions.
- **Activity history and comments:** Keep track of updates and team discussions.
- **Data consistency:** Optimistic concurrency checks help prevent stale updates, while claim handling protects against duplicate claims.
- **Automated tests:** Pytest coverage for important API behaviours.
- **Docker setup:** Run the frontend, backend, and PostgreSQL database together.

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite |
| Backend | Python, FastAPI |
| Database | PostgreSQL, SQLAlchemy |
| Authentication | JWT |
| Testing | Pytest |
| Development | Docker, Docker Compose |

## 🚀 Getting Started

### Prerequisites

- Docker Desktop with Docker Compose
- Git

### Run Locally

1. Clone the repository:

   ```bash
   git clone https://github.com/aadi1828/Newtonite_project.git
   cd Newtonite_project
   ```

2. Copy `.env.example` to `.env` and review the configuration.

3. Start the application:

   ```bash
   docker compose up --build
   ```

4. Open the application:

   - **Frontend:** http://localhost:5173
   - **API documentation:** http://localhost:8000/docs

Keep the terminal running while using the application.

## 🔐 Demo Accounts

All seeded demo accounts use the following password:

`NewtoniteDemo!2026`

| Role | Email |
|---|---|
| Admin | `admin@newtonite.local` |
| Lead | `lead@newtonite.local` |
| Member | `member@newtonite.local` |
| Viewer | `viewer@newtonite.local` |
| Separate-team member | `outsider@newtonite.local` |

These credentials are for local evaluation only. Do not use them for a public production deployment.

## 🧪 Running the Tests

With the application running, open another terminal in the repository root and execute:

```bash
docker compose exec backend python -m pytest -q
```

**Verified result:** 6 tests passed.

The tests cover login, cross-team access restrictions, stale-update rejection, one-time claiming, and invalid workflow transitions.

## 📁 Project Structure

```text
Newtonite_project/
├── backend/
│   ├── app/
│   ├── tests/
│   └── requirements.txt
├── frontend/
├── docker-compose.yml
├── .env.example
├── ENGINEERING_DECISIONS.md
├── KNOWN_LIMITATIONS.md
└── README.md
```

## 🧠 Engineering Decisions

The project uses a separate frontend and backend to keep the interface and business logic independent. FastAPI provides the REST API, PostgreSQL stores application data, and Docker Compose simplifies local setup.

Team-based authorization, workflow validation, concurrency checks, and activity tracking address common challenges in multi-user operations systems.

For more detail, see [ENGINEERING_DECISIONS.md](ENGINEERING_DECISIONS.md).

## ⚠️ Known Limitations

This is an assessment MVP, not a production-ready enterprise application. It does not currently include features such as SSO, email notifications, file attachments, WebSockets, or a distributed background worker.

Review [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for additional details.

## 👨‍💻 About This Project

I built Newtonite Operations to demonstrate my understanding of full-stack development, API design, database integration, authorization, and backend testing. The goal was to create a practical application that is easy to run, explore, and evaluate.

Feedback and suggestions are welcome.
