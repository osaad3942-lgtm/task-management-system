# Task Management System

A production-ready RESTful API built with **FastAPI**, **SQL Server**, and **Redis** for managing projects and tasks with role-based access control, JWT authentication, request logging, caching, and an in-memory monitoring dashboard.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Features](#features)
- [Role-Based Access Control](#role-based-access-control)
- [API Endpoints](#api-endpoints)
- [Data Models](#data-models)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Setup](#local-setup)
  - [Docker Setup](#docker-setup)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [Monitoring](#monitoring)
- [Caching Strategy](#caching-strategy)
- [Logging](#logging)
- [Known Limitations & Future Improvements](#known-limitations--future-improvements)

---

## Overview

The Task Management System allows organizations to manage projects and their associated tasks across a three-tier user hierarchy: **Admin**, **Manager**, and **Employee**. Each role has well-defined permissions to create, view, update, and delete resources. The API is secured with JWT bearer tokens and uses Redis for task-list caching to reduce database load.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI App                       │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │  /auth   │  │/projects │  │      /tasks        │ │
│  └──────────┘  └──────────┘  └────────────────────┘ │
│                                                     │
│  ┌─────────────────────────────────────────────────┐ │
│  │         Middleware: LoggingMiddleware            │ │
│  │         (request/response logging + metrics)    │ │
│  └─────────────────────────────────────────────────┘ │
│                                                     │
│  ┌──────────────────┐    ┌───────────────────────┐  │
│  │  SQLAlchemy ORM  │    │    Redis Cache        │  │
│  │  (SQL Server)    │    │  (task list caching)  │  │
│  └──────────────────┘    └───────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer         | Technology                          |
|---------------|-------------------------------------|
| Framework     | FastAPI                             |
| Database      | Microsoft SQL Server (via pyodbc)   |
| ORM           | SQLAlchemy                          |
| Auth          | JWT (python-jose) + bcrypt          |
| Cache         | Redis                               |
| Templating    | Jinja2                              |
| Testing       | Pytest + HTTPX TestClient           |
| Server        | Uvicorn (ASGI)                      |
| Containerization | Docker + Docker Compose          |

---

## Project Structure

```
task-management-system/
├── app/
│   ├── core/
│   │   ├── config.py            # App configuration (env vars)
│   │   ├── database.py          # SQLAlchemy engine, session, Base
│   │   ├── security.py          # Password hashing + JWT creation
│   │   ├── jwt_handler.py       # JWT decode utilities
│   │   └── redis_client.py      # Redis get/set/delete helpers
│   ├── dependencies/
│   │   ├── auth.py              # get_current_user dependency
│   │   └── roles.py             # require_role() factory dependency
│   ├── middleware/
│   │   └── logging_middleware.py # Request/response logging + metrics
│   ├── models/
│   │   ├── user.py              # User SQLAlchemy model
│   │   ├── project.py           # Project SQLAlchemy model
│   │   └── task.py              # Task SQLAlchemy model
│   ├── routes/
│   │   ├── auth.py              # /register, /login
│   │   ├── projects.py          # CRUD for projects
│   │   ├── tasks.py             # CRUD for tasks
│   │   └── monitoring.py        # /monitoring, /dashboard
│   ├── schemas/
│   │   ├── user_schema.py       # Pydantic user schemas
│   │   ├── project_schema.py    # Pydantic project schemas
│   │   └── task_schema.py       # Pydantic task schemas
│   ├── services/
│   │   ├── auth_service.py      # Auth business logic
│   │   ├── project_service.py   # Project business logic
│   │   └── task_service.py      # Task business logic + RBAC
│   ├── templates/
│   │   └── dashboard.html       # Monitoring HTML dashboard
│   ├── utils/
│   │   ├── helpers.py           # Status transition validation
│   │   ├── logger.py            # Structured logger setup
│   │   └── metrics.py           # In-memory metrics tracker
│   └── main.py                  # App factory + router registration
├── tests/
│   ├── test_api.py              # Integration tests (auth, tasks, projects)
│   ├── test_auth.py
│   ├── test_projects.py
│   └── test_tasks.py
├── alembic/                     # Database migrations (Alembic)
├── logs/
│   └── app.log                  # Application log output
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env
```

---

## Features

- **JWT Authentication** — Stateless bearer token auth with 60-minute expiry
- **Role-Based Access Control (RBAC)** — Three-tier role system with enforced permissions at the service layer
- **Redis Caching** — Task list responses cached per user/role for 10 minutes; cache invalidated on mutations
- **Status Transition Validation** — Tasks follow an enforced workflow (`todo → in_progress → done`)
- **Request Logging Middleware** — Every request and response is logged with timing, method, path, and status code
- **In-Memory Metrics** — Tracks total requests, success/error counts, average response time, and recent errors
- **Monitoring Dashboard** — HTML dashboard at `/dashboard` rendered via Jinja2 with live metrics
- **CORS** — Enabled for all origins (configurable for production)
- **Structured Logging** — JSON-friendly log format including user IDs, roles, and operation outcomes
- **Cascade Deletes** — Deleting a project cascades to all its tasks; deleting a user nullifies assignments

---

## Role-Based Access Control

| Action                  | admin | manager | employee |
|-------------------------|-------|---------|----------|
| Register/Login          | ✅    | ✅      | ✅       |
| Create Project          | ✅    | ❌      | ❌       |
| View All Projects       | ✅    | ✅      | ❌       |
| Update Project          | ✅    | ❌      | ❌       |
| Delete Project          | ✅    | ❌      | ❌       |
| Create Task             | ✅    | ✅      | ❌       |
| View All Tasks          | ✅    | ✅      | ❌       |
| View Own Assigned Tasks | ✅    | ✅      | ✅       |
| Update Task (all fields)| ✅    | ✅      | ❌       |
| Update Task (status only)| ✅   | ✅      | ✅ (own) |
| Delete Task             | ✅    | ✅      | ❌       |
| Assign Task to Employee | ✅    | ✅      | ❌       |

> **Note:** Tasks can only be assigned to users with the `employee` role.

---

## API Endpoints

### Auth

| Method | Path        | Description              | Auth Required |
|--------|-------------|--------------------------|---------------|
| POST   | `/register` | Register a new user      | ❌            |
| POST   | `/login`    | Login and receive JWT    | ❌            |

**Register Request (query params):**
```
name=John Doe&email=john@example.com&password=secret&role=employee
```

**Login Response:**
```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer"
}
```

---

### Projects

| Method | Path                   | Description            | Role Required     |
|--------|------------------------|------------------------|-------------------|
| POST   | `/projects`            | Create a project       | admin             |
| GET    | `/projects`            | List all projects      | admin, manager    |
| GET    | `/projects/{id}`       | Get a single project   | admin, manager    |
| PUT    | `/projects/{id}`       | Update a project       | admin             |
| DELETE | `/projects/{id}`       | Delete a project       | admin             |

**Project Payload:**
```json
{
  "name": "Website Redesign",
  "description": "Full redesign of the company website"
}
```

---

### Tasks

| Method | Path             | Description             | Role Required              |
|--------|------------------|-------------------------|----------------------------|
| POST   | `/tasks`         | Create a task           | admin, manager             |
| GET    | `/tasks`         | List tasks              | admin/manager: all; employee: own |
| GET    | `/tasks/{id}`    | Get a single task       | own or admin/manager       |
| PUT    | `/tasks/{id}`    | Update a task           | admin/manager: full; employee: status only |
| DELETE | `/tasks/{id}`    | Delete a task           | admin, manager             |

**Task Create Payload:**
```json
{
  "title": "Build login page",
  "description": "Implement the login UI",
  "project_id": 1,
  "assignee_id": 5,
  "priority": "high"
}
```

**Task Status Values:** `todo` → `in_progress` → `done`

**Task Priority Values:** `low`, `medium`, `high`

---

### Monitoring

| Method | Path          | Description                         | Auth Required |
|--------|---------------|-------------------------------------|---------------|
| GET    | `/monitoring` | JSON metrics (requests, errors, etc.)| ❌           |
| GET    | `/dashboard`  | HTML monitoring dashboard            | ❌           |

**Monitoring Response:**
```json
{
  "system_health": "running",
  "uptime_seconds": 3600.5,
  "total_requests": 120,
  "successful_requests": 115,
  "error_requests": 5,
  "average_response_time_seconds": 0.043,
  "recent_errors": [...]
}
```

---

## Data Models

### User
| Column     | Type        | Notes                          |
|------------|-------------|--------------------------------|
| id         | Integer PK  |                                |
| name       | String(100) | Required                       |
| email      | String(150) | Unique, required               |
| password   | String      | Bcrypt hashed                  |
| role       | String(20)  | `admin`, `manager`, `employee` |
| created_at | DateTime    |                                |

### Project
| Column      | Type        | Notes                        |
|-------------|-------------|------------------------------|
| id          | Integer PK  |                              |
| name        | String(150) | Required                     |
| description | Text        | Optional                     |
| created_by  | FK → users  | SET NULL on user delete      |
| created_at  | DateTime    |                              |

### Task
| Column      | Type        | Notes                              |
|-------------|-------------|------------------------------------|
| id          | Integer PK  |                                    |
| title       | String(150) | Required                           |
| description | Text        | Optional                           |
| status      | String(20)  | Default: `todo`                    |
| priority    | String(20)  | Default: `medium`                  |
| project_id  | FK → projects | CASCADE on project delete        |
| assignee_id (user_id) | FK → users | SET NULL on user delete  |
| created_at  | DateTime    |                                    |
| updated_at  | DateTime    |                                    |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Microsoft SQL Server (with `ODBC Driver 17 for SQL Server`)
- Redis 6+
- Docker & Docker Compose (for containerized setup)

---

### Local Setup

**1. Clone the repository**
```bash
git clone https://github.com/your-org/task-management-system.git
cd task-management-system
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate       # Linux/macOS
venv\Scripts\activate          # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure the database connection**

Edit `app/core/database.py` (or use environment variables once `.env` is configured) to point to your SQL Server instance:

```python
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=<your_server>;"
    "DATABASE=Task_Management;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)
```

**5. Configure Redis**

Ensure Redis is running locally on port `6379`. The client is configured in `app/core/redis_client.py`.

**6. Run the application**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**7. Open the interactive API docs**

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Docker Setup

```bash
docker-compose up --build
```

This starts three services:
- `api` — FastAPI app on port `8000`
- `redis` — Redis on port `6379`
- `db` — SQL Server on port `1433`

> See [Environment Variables](#environment-variables) for required `.env` values before running Docker.

---

## Environment Variables

Create a `.env` file in the project root with the following values:

```env
# Database
DB_SERVER=db
DB_NAME=Task_Management
DB_USER=sa
DB_PASSWORD=YourStrong!Passw0rd

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

> **Security Warning:** Never commit `.env` to version control. The current hardcoded `SECRET_KEY` in `app/core/security.py` must be replaced with an environment variable before deploying to production.

---

## Running Tests

```bash
pytest tests/ -v
```

The test suite uses FastAPI's `TestClient` (backed by HTTPX) and covers:
- Home endpoint health check
- User registration (duplicate prevention)
- Admin login and token issuance
- Task CRUD with role enforcement
- Project CRUD with role enforcement

> **Note:** Integration tests connect to the real database. Ensure SQL Server and Redis are running, or mock them for CI pipelines.

---

## Monitoring

The app tracks in-memory metrics via the `LoggingMiddleware`:

- **`GET /monitoring`** — Returns a JSON payload with uptime, request counts, error rate, and average response time.
- **`GET /dashboard`** — Renders an HTML dashboard with the same metrics using Jinja2 templates.

Metrics are reset when the server restarts (in-memory only). For persistent metrics, integrate with Prometheus or an external APM.

---

## Caching Strategy

Task list responses (`GET /tasks`) are cached in Redis with a key format of:

```
tasks_{role}_{user_id}
```

- **TTL:** 600 seconds (10 minutes)
- **Invalidation:** Cache is cleared on task create, update, or delete for the acting user's cache key.

> The cache is role-aware: admin/manager caches contain all tasks, while employee caches contain only their assigned tasks.

---

## Logging

Logs are written to `logs/app.log` and stdout using Python's `logging` module. Each log entry includes:

- Timestamp
- Log level
- User ID and role (where applicable)
- Operation context (e.g., `Login attempt | email=...`)
- Outcome (`success`, `failed`, `forbidden`)

Log levels used:
- `DEBUG` — DB query details
- `INFO` — Successful operations
- `WARNING` — Business rule violations, auth failures
- `ERROR` — Unexpected exceptions (handled by middleware)

---

## Known Limitations & Future Improvements

| Area | Current State | Recommended Improvement |
|------|---------------|--------------------------|
| Secret Key | Hardcoded in `security.py` | Load from `.env` / secrets manager |
| Database | Local SQL Server (Windows auth) | Use env-based connection string; support PostgreSQL |
| Auth | No token refresh or revocation | Implement refresh tokens + Redis blocklist |
| Caching | Single-user key invalidation | Broader cache invalidation on cross-user mutations |
| Monitoring | In-memory only; resets on restart | Integrate Prometheus + Grafana |
| Migrations | Alembic folder present but unused | Wire up Alembic migrations; remove `create_all` from startup |
| Tests | Integration tests require live DB | Add unit tests with mocked DB; separate CI fixtures |
| CORS | `allow_origins=["*"]` | Restrict to known origins in production |
| Pagination | No pagination on list endpoints | Add `skip` / `limit` query params |
| Input Validation | Role passed as plain string on register | Validate against an enum; prevent arbitrary role assignment |
