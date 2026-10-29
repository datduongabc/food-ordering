# DaTeNO Restaurant - Online Ordering & Table Booking

[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)](#tech-stack)
[![Frontend](https://img.shields.io/badge/Frontend-React_%2B_TypeScript-3178C6)](#tech-stack)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1)](#quick-start-with-docker--postgresql)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)](#quick-start-with-docker--postgresql)

**DaTeNO** is a restaurant web app for ordering food for delivery and booking tables across three branches. A **FastAPI** backend serves a JSON API to a **React + TypeScript** single-page app, with **PostgreSQL** for storage. The whole interface is available in Vietnamese (default) and English.

> This branch replaces the original PHP application, which remains on `main`. The PHP sources (`app/`, `public/`, `config/`, `tests/*.php`) are still in the tree until the migration is merged.

---

## Key Features

### Accounts & Security
- **Sign-up and sign-in** with Argon2 password hashing and server-side sessions in HTTP-only cookies; "remember me" keeps a session for 7 days.
- **Email verification and password reset** with 6-digit codes that expire after 15 minutes and lock after 5 wrong tries.
- **Brute-force protection:** an account locks for 15 minutes after 5 failed sign-ins.
- **CSRF protection** on every state-changing request.
- **Guest cart merge:** a cart built before signing in is kept in the browser and merged into the account on sign-in.

### Menu & Reviews
- **Bilingual catalog:** every dish, category and branch has a Vietnamese and an English name; switching language is instant.
- **Filtering, sorting and pagination** kept in the URL, so a filtered menu can be shared and reloaded.
- **Search** matches dish names in both languages ("gỏi" or "spring rolls").
- **Reviews:** one 1-5 star review per customer per dish, averaged on the menu.

### Ordering & Payment
- **Checkout** with delivery details pre-filled from the account; each branch card warns about dishes it does not serve.
- **Cash on delivery or MoMo.** MoMo runs as a **sandbox** that simulates approval or decline; no real payments are made, and it is switched off outside local mode.
- **Change of mind:** a pending cash order can be paid with MoMo, and an unpaid MoMo order can go back to cash.
- **Order history** with a status timeline that says who made each change (customer, restaurant or system); pending orders can be cancelled.
- Prices are stored and shown in whole Vietnamese dong.

### Table Booking
- Book from today up to 3 days ahead, in half-hour seatings from 10:00 to 21:00, for up to 10 guests.
- Customers see and cancel their pending bookings from their account.

### Admin Console (`/admin`)
- **Overview:** revenue, average order value, pending orders and bookings, a daily revenue chart, best and slowest sellers, MoMo success rate and lowest-rated dishes, over 7, 30 or 90 days.
- **Orders:** filter by status; confirm, mark delivered or cancel, with a note for the customer.
- **Bookings:** filter by status and date; confirm, mark arrived or cancel.
- **Dishes:** add and edit in both languages, set price, category and branches, upload a photo, hide and restore.
- **Users:** search, add, change role, verification and password, deactivate and restore (never your own account).

---

## Architecture

```text
Browser (React SPA)
      |
      v
nginx  (serves the built app; proxies /api and /media, so cookies stay first-party)
      |
      v
FastAPI (backend/app)
  modules/<feature>/router.py   HTTP endpoints and request/response schemas
  modules/<feature>/service.py  business rules, validation, transactions
  modules/<feature>/models.py   SQLAlchemy models
      |
      v
PostgreSQL 16  (schema and seed data managed by Alembic migrations)
```

Every API error carries a stable `code` and `params`, which the frontend translates into the selected language.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python 3.14, FastAPI, SQLAlchemy 2, Alembic, Pydantic, pwdlib (Argon2), uv |
| **Frontend** | React 19, TypeScript, Vite, React Router, TanStack Query, React Hook Form, Zod |
| **Database** | PostgreSQL 16 (SQLite also works for development and tests) |
| **Testing** | pytest, Vitest, Testing Library, MSW, Playwright |
| **DevOps** | Docker, Docker Compose, nginx, GitHub Actions |

---

## Quick Start with Docker & PostgreSQL

Docker Compose runs three containers: PostgreSQL (`postgres:16-alpine`), the FastAPI backend (which applies the Alembic migrations, including the menu seed, on every start) and the React app served by nginx, which also proxies `/api` and `/media` to the backend.

### 1. Clone the repository & configure environment
```bash
git clone <repository-url>
cd restaurant_project
cp .env.example .env
# Set SECRET_KEY in .env, e.g. python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 2. Build and start the containers
```bash
docker compose up -d --build
```

- **Web Application:** [http://localhost:8000](http://localhost:8000)
- **Admin (local mode only):** `datduongtandat385@gmail.com` / `12345678`
- **Sign-up codes (local mode):** printed by `docker compose logs -f backend`
- **PostgreSQL Database:** `localhost:5432` (Database: `dateno`, User and Password from `.env`)

### 3. Stop the containers
```bash
docker compose down
```
*(To wipe the database and uploaded photos and start from the seed again, run `docker compose down -v`.)*

### Configuration

All settings live in `.env`; see [`.env.example`](.env.example).

- **`APP_ENV=local`** prints emails to the backend log, enables the MoMo sandbox, marks cookies non-Secure for plain HTTP and seeds the admin above. Use `production` only behind HTTPS; it seeds no admin, so create one with `docker compose exec backend python -m app.cli create-admin --email ... --name ... --phone ...`.
- **Database password with special characters:** keep the raw password in `DB_PASSWORD` (Postgres uses it to create the user) and also set `DATABASE_URL` with the password URL-encoded (the backend connects with it).
- **Real emails:** set `SMTP_USERNAME` to a Gmail address and `SMTP_PASSWORD` to a Google [App Password](https://myaccount.google.com/apppasswords); `MAIL_FROM` defaults to the username.

---

## Local Development (Without Docker)

Requires [uv](https://docs.astral.sh/uv/) and Node.js 22.

**Backend** (http://127.0.0.1:8000):
```bash
cd backend
uv sync
cp .env.example .env        # set SECRET_KEY and DATABASE_URL
                            # (SQLite also works: DATABASE_URL=sqlite:///./dateno.db)
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

**Frontend** (http://localhost:5173, proxying `/api` and `/media` to the backend):
```bash
cd frontend
npm ci
npm run dev
```

Docker Compose also publishes port 8000; stop it, or set `WEB_PORT` in `.env`, before running the backend this way. To point the dev server at another backend, set `DATENO_API_URL`.

---

## Testing

**Backend** (`backend/tests`: unit, integration and end-to-end against a real uvicorn server):
```bash
cd backend
uv run pytest                                   # SQLite
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/dateno_test uv run pytest
uv run ruff check . && uv run ruff format --check .
```

**Frontend** (`frontend/tests`):
```bash
cd frontend
npm run typecheck && npm run lint && npm run format:check
npm test             # unit and integration (Vitest, Testing Library, MSW)
npx playwright install chromium   # once
npm run test:e2e     # Playwright on desktop and mobile, against the real backend
```

The end-to-end suite migrates a throwaway SQLite database, starts the backend and serves a production build. Set `E2E_DATABASE_URL` to an empty Postgres database to run it on Postgres instead.

---

## CI/CD Pipeline

GitHub Actions runs on every push and pull request:

- **[`backend.yml`](.github/workflows/backend.yml):** ruff lint and format, migrations up, `alembic check` and back down on Postgres 16, then the test suite on SQLite and on Postgres.
- **[`frontend.yml`](.github/workflows/frontend.yml):** type check, lint, format, unit and integration tests, then the Playwright suite against the real backend.
- **[`ci.yml`](.github/workflows/ci.yml):** the legacy PHP checks, then validates `docker-compose.yml` and builds its images.

---

## Project Structure

```text
restaurant_project/
├── backend/
│   ├── app/
│   │   ├── core/              # Settings, database, sessions & security, CSRF, errors, email
│   │   ├── modules/           # auth, catalog, cart, orders (incl. MoMo sandbox),
│   │   │                      # reservations, feedback, users, admin
│   │   ├── cli.py             # create-admin command
│   │   └── main.py            # FastAPI application
│   ├── alembic/versions/      # Schema migrations and seed data (menu, local admin)
│   ├── media/products/        # Seeded dish photos; uploads are added here
│   ├── tests/                 # unit/, integration/, e2e/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/               # Routes, providers, query client
│   │   ├── components/        # Layout, form fields and UI building blocks
│   │   ├── features/          # account, admin, auth, cart, catalog, home,
│   │   │                      # orders, reservations, reviews
│   │   ├── i18n/              # Vietnamese and English dictionaries
│   │   └── lib/               # API client, formatting
│   ├── tests/                 # unit/, integration/, e2e/
│   ├── nginx.conf             # Production server and API proxy
│   └── Dockerfile
├── .github/workflows/         # backend.yml, frontend.yml, ci.yml
├── docker-compose.yml         # PostgreSQL + backend + web
└── .env.example
```

---

## License

Copyright (c) 2026 DaTeNO Restaurant. All rights reserved.
