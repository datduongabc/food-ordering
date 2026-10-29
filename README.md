# DaTeNO Restaurant - Online Ordering & Table Booking

[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)](#tech-stack)
[![Frontend](https://img.shields.io/badge/Frontend-React_%2B_TypeScript-3178C6)](#tech-stack)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1)](#quick-start-with-docker--postgresql)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)](#quick-start-with-docker--postgresql)

**DaTeNO** is a restaurant web app for ordering food for delivery and booking tables across three branches. A **FastAPI** backend serves a JSON API to a **React + TypeScript** single-page app, with **PostgreSQL** for storage. The whole interface is available in Vietnamese (default) and English.

> This replaces the original PHP application, which is kept in the git history.

---

## Key Features

### Accounts & Security
- **Sign-up and sign-in** with Argon2 password hashing and server-side sessions in HTTP-only cookies; "remember me" keeps a session for 7 days.
- **Email verification and password reset** with 6-digit codes that expire after 15 minutes and lock after 5 wrong tries.
- **Brute-force protection:** 5 failed sign-ins for one email from one address block that pair for 15 minutes. Unknown emails are blocked the same way, and no account is ever locked, so neither the block nor the error reveals whether an account exists, and nobody can lock someone else out.
- **No account discovery through sign-in or password reset:** wrong passwords and unknown emails get the same answer in the same time; reset requests always get the same reply; and a reset for an unknown email runs out of tries exactly like a real code.
- **CSRF protection** on every state-changing request.
- **Rate limits** per client address on the whole API (300 reads and 60 writes a minute), with tighter ones where abuse costs most: sign-in (10/min), sign-up (5/hour), password-reset and verification emails (3 per inbox or account every 15 min), code entry, orders, payments, bookings and reviews. Over the limit the API answers `429` with a `Retry-After` header.
- **Hardened responses:** a Content-Security-Policy, `nosniff`, no framing, a strict referrer policy and `no-store` on API answers; API docs are only served outside production, and production refuses to start without a random `SECRET_KEY` of at least 32 characters.
- **Guest cart merge:** a cart built before signing in is kept in the browser and merged into the account on sign-in.

### Menu & Reviews
- **Bilingual catalog:** every dish, category and branch has a Vietnamese and an English name; switching language is instant.
- **Filtering, sorting and pagination** kept in the URL, so a filtered menu can be shared and reloaded.
- **Search** matches dish names in both languages ("gỏi" or "spring rolls").
- **Reviews:** one 1-5 star review per customer per dish, averaged on the menu.

### Ordering & Payment
- **Checkout** with delivery details pre-filled from the account; each branch card warns about dishes it does not serve.
- **Cash on delivery or MoMo.** With MoMo keys set, customers pay on MoMo's own page; the result comes back both server to server (IPN) and through the customer's return, each checked against MoMo's HMAC signature and the order total, and applied only once. Without keys, local mode offers a **sandbox** that simulates approval or decline, and production offers cash only.
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

- **`APP_ENV=local`** prints emails to the backend log, enables the MoMo sandbox when no MoMo keys are set, marks cookies non-Secure for plain HTTP and seeds the admin above. Use `production` only behind HTTPS; it seeds no admin, so create one with `docker compose exec backend python -m app.cli create-admin --email ... --name ... --phone ...`.
- **Database password with special characters:** keep the raw password in `DB_PASSWORD` (Postgres uses it to create the user) and also set `DATABASE_URL` with the password URL-encoded (the backend connects with it).
- **MoMo:** register at [business.momo.vn](https://business.momo.vn), copy the test environment's partner code, access key and secret key into `MOMO_PARTNER_CODE`, `MOMO_ACCESS_KEY` and `MOMO_SECRET_KEY`, and set `PUBLIC_URL` to the address customers use. MoMo must be able to reach `PUBLIC_URL/api/payments/momo/ipn`; on a development machine it cannot, and results arrive only when the customer returns to the site. Switch `MOMO_ENDPOINT` to `https://payment.momo.vn` with production keys to take real money.
- **Real emails:** set `SMTP_USERNAME` to a Gmail address and `SMTP_PASSWORD` to a Google [App Password](https://myaccount.google.com/apppasswords); `MAIL_FROM` defaults to the username.

### Known Security Limitations

- **Sign-up reveals taken emails and phone numbers.** It answers `email_taken` or `phone_taken`, so anyone can check whether an address has an account. Closing this needs a sign-up that always replies "check your inbox" and tells an existing owner by email instead, and phone numbers would still give it away.
- **Guesses spread over many addresses are not stopped.** Failed sign-ins are counted per address and email, never per account, by design: a per-account lock leaks which accounts exist and lets anyone lock a customer out. Someone with many IPs can therefore keep guessing one account's password slowly; the 8-character minimum is the remaining defence.
- **Counters live in one process's memory.** Rate limits, failed sign-ins and the stand-in reset codes for unknown emails reset when the backend restarts, and several backend processes or replicas would each count separately. Scaling out needs a shared store such as Redis first.
- **Small timing differences remain.** A reset request for a real account writes a code to the database and one for an unknown email does not; the difference is a few milliseconds, well inside normal network jitter, but it is not zero.
- **Client addresses come from the proxy.** The bundled nginx overwrites `X-Forwarded-For`; behind another proxy or load balancer, make sure it does too, or visitors share one address (or can pick their own).
- **Late MoMo charges need a manual refund.** If MoMo charges an attempt the customer already abandoned (a retry or a switch to cash) or an order cancelled meanwhile, the backend logs an error instead of changing the order; refund it from the MoMo portal. There is no automatic reconciliation with MoMo's query API, so a payment whose IPN and return were both lost stays unpaid until checked by hand.
- **No HSTS yet.** Add `Strict-Transport-Security` to `frontend/security-headers.conf` once the site is served over HTTPS.

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
uv run pytest --cov                             # with coverage (fails under 85%)
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/dateno_test uv run pytest
uv run ruff check . && uv run ruff format --check .
```

**Frontend** (`frontend/tests`):
```bash
cd frontend
npm run typecheck && npm run lint && npm run format:check
npm test             # unit and integration (Vitest, Testing Library, MSW)
npm test -- --coverage   # with coverage (fails under 85% of lines and statements, 80% of branches and functions)
npx playwright install chromium   # once
npm run test:e2e     # Playwright on desktop and mobile, against the real backend
```

The end-to-end suite migrates a throwaway SQLite database, starts the backend and serves a production build. Set `E2E_DATABASE_URL` to an empty Postgres database to run it on Postgres instead.

---

## CI/CD Pipeline

GitHub Actions runs on every push and pull request:

- **[`backend.yml`](.github/workflows/backend.yml):** ruff lint and format, migrations up, `alembic check` and back down on Postgres 16, then the test suite on SQLite (with an 85% coverage gate) and on Postgres.
- **[`frontend.yml`](.github/workflows/frontend.yml):** type check, lint, format, unit and integration tests with coverage thresholds, then the Playwright suite against the real backend.
- **[`ci.yml`](.github/workflows/ci.yml):** validates `docker-compose.yml` and builds its images.

---

## Project Structure

```text
restaurant_project/
├── backend/
│   ├── app/
│   │   ├── core/              # Settings, database, sessions & security, CSRF, rate limits, headers, email
│   │   ├── modules/           # auth, catalog, cart, orders (incl. MoMo and its sandbox),
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
├── .github/workflows/         # backend.yml, frontend.yml, ci.yml (Docker)
├── docker-compose.yml         # PostgreSQL + backend + web
└── .env.example
```

---

## License

Copyright (c) 2026 DaTeNO Restaurant. All rights reserved.
