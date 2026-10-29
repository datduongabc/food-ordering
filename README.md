# DaTeNO Restaurant - Management & Online Ordering System

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF)](#cicd-pipeline)
[![PHP](https://img.shields.io/badge/PHP-8.2%2B-777BB4)](#tech-stack)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1)](#quick-start-with-docker--postgresql)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)](#quick-start-with-docker--postgresql)
[![Coverage](https://img.shields.io/badge/Test_Coverage-%3E%3D85%25-brightgreen)](#testing--code-coverage)

**DaTeNO** is a full-stack web application built for modern restaurant operations, online food ordering, and table reservations. Engineered from the ground up using a **Modular PHP MVC + Service Layer Architecture**, it combines strict backend security, transactional database integrity with **PostgreSQL**, and responsive frontend interactions powered by the **Native Fetch API (`async/await` & `AbortController`)**.

---

## Key Features

### Authentication & Account Security
- **Registration & Sign-In:** Server-side and client-side validation with bcrypt password hashing (`password_hash`).
- **Email Verification & OTP Recovery:** Time-limited (15-minute), SHA-256 hashed tokens delivered via **PHPMailer (SMTP)** for account activation, forgot-password recovery, and password changes.
- **Brute-Force Protection:** Enforces a strict 5-attempt limit per token both in application logic and via database `CHECK` constraints.
- **"Remember Me" Persistent Sessions:** Uses HTTP-only cookies backed by SHA-256 database tokens and automatic guest-cart synchronization upon sign-in.

### Interactive Menu, Live Search & Reviews
- **Dynamic Menu Catalog:** Displays dishes with branch availability, category badges, and real-time star ratings (`average_rating`).
- **Asynchronous Filtering, Sorting & Pagination:** Powered by the **Native Fetch API**, `AbortController` (automatically cancelling stale in-flight requests to prevent race conditions), and the browser **History API** (`pushState` / `popstate`).
- **Debounced Live Search:** Instant dish lookup with a 300ms debounce and race-condition cancellation.
- **Customer Reviews:** Authenticated diners can rate dishes (1-5 stars) and post reviews, automatically recalculating dish ratings via database triggers.

### Shopping Cart, Transactional Ordering & MoMo Payment Gateway
- **Hybrid Guest & User Cart:** Guests can add dishes to a session-backed cart that seamlessly merges into their persistent database cart (`cart_items`) upon signing in.
- **Asynchronous Cart Actions:** Instant "Add to Cart" buttons with real-time header badge updates and Bootstrap 5 Toast notifications.
- **MoMo E-Wallet & QR Payment Gateway (v2 API):** Supports HMAC-SHA256 request signing, automatic USD-to-VND currency conversion, interactive QR checkout portal, and cryptographically verified Return URL / IPN callbacks (`PAID`, `UNPAID`, `FAILED`) alongside Cash on Delivery (`COD`).
- **ACID Order Checkout:** Places food orders inside a **PDO Database Transaction** (`orders` + `order_items`) and provides an activity dashboard (`?page=orders`) for customers to pay via MoMo, track fulfillment, or cancel `PENDING` orders.

### Table Reservation System
- **Multi-Branch Booking:** Customers can book tables up to 10 days in advance across restaurant locations with automatic profile pre-fill and anti-spam submission locking.
- **Self-Service Management:** Customers can view and cancel upcoming `PENDING` table bookings directly from their account.

### Role-Based Admin Dashboard (RBAC)
- **Analytics Dashboard:** Real-time KPIs for completed revenue, total orders, pending bookings, active menu items, and registered users.
- **Product Management (Full CRUD):** Create and edit dishes, upload `.webp`/`.jpg`/`.png` images, assign branch availability (`product_availabilities`), and soft-delete or restore items.
- **Order & Reservation Management:** Filter by status (`PENDING`, `CONFIRMED`, `COMPLETED`, `CANCELLED`), inspect itemized order modals, and update fulfillment states.
- **User Management:** Create users, manage roles (`CUSTOMER` / `ADMIN`), toggle email verification, and deactivate/restore accounts with self-lockout protection.

---

## System Architecture

The application follows a strict separation of concerns across four layers:

```text
HTTP Request --> Front Controller (public/index.php)
                      |
                      v
               Central Router (app/core/Router.php)
                      |
                      v
             Module Controller (Handles HTTP, Session & View selection)
                      |
                      v
              Service Layer (Business logic, validation, formatting, SMTP)
                      |
                      v
               Model Layer (Prepared PDO SQL statements & transactions)
                      |
                      v
         Singleton Database (app/core/Database.php --> PostgreSQL / MySQL)
```

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | PHP 8.2+ (Custom Modular MVC + Service Layer) |
| **Database** | PostgreSQL 16 (Primary via Docker) / MySQL 8.x & SQLite compatible via PDO |
| **Frontend** | HTML5, CSS3, Bootstrap 5.3, Vanilla JavaScript ES6+ (`fetch`, `async/await`, `AbortController`) |
| **Libraries** | `phpmailer/phpmailer` (^7.0), `vlucas/phpdotenv` (^5.6) |
| **DevOps & QA** | Docker, Docker Compose, PHPUnit 10.5, GitHub Actions CI/CD |

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

---

## Local Installation (Without Docker)

1. **Install dependencies via Composer:**
   ```bash
   composer install
   ```
2. **Configure `.env`:**
   Copy `.env.example` to `.env` and update your database (`DB_CONNECTION=pgsql` or `mysql`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`) and SMTP credentials (`MAIL_EMAIL`, `MAIL_PASSWORD`).
3. **Import Database Schema & Seed Data:**
   - **PostgreSQL:** `psql -U postgres -d food_ordering_db -f config/init_postgres.sql`
   - **MySQL:** `mysql -u root -p food_ordering_db < config/dump.sql`
4. **Run the built-in PHP server:**
   ```bash
   php -S localhost:8000 -t public
   ```

---

## Testing & Code Coverage

The project includes a comprehensive **PHPUnit 10** test suite covering core utilities, authentication workflows, menu sorting/filtering, product CRUD, reviews, guest/user cart synchronization, transactional order checkout, and table reservations.

```bash
# Run the full test suite
composer test

# Run tests with code coverage report (requires Xdebug)
composer test:coverage
```

---

## CI/CD Pipeline

The GitHub Actions workflow ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) automatically runs on every push and pull request to `main`, `master`, or `develop`:
1. **Service Provisioning:** Starts an isolated `postgres:16-alpine` service container with healthchecks.
2. **Static Analysis & Linting:** Validates `composer.json` and runs `php -l` syntax checks across all PHP files in `app/`, `config/`, `public/`, and `tests/`.
3. **Automated Tests & Coverage Gate:** Executes the PHPUnit test suite against PostgreSQL and enforces a minimum code coverage threshold (>= 80%).
4. **Docker Verification:** Validates `docker-compose.yml` and builds the production Docker image.

---

## Project Structure

```text
restaurant_project/
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI/CD pipeline
├── app/
│   ├── core/
│   │   ├── Database.php            # Singleton PDO connection (PostgreSQL / MySQL / SQLite)
│   │   ├── Helpers.php             # URL, XSS escaping, CSRF, Currency & Cart helpers
│   │   ├── Router.php              # Central query-based MVC router & RBAC middleware
│   │   └── views/layouts/          # Shared Header & Footer templates
│   └── modules/
│       ├── auth/                   # Sign-in, Sign-up, Remember Me, OTP & Password Reset
│       ├── cart/                   # Guest & User shopping cart management
│       ├── feedback/               # Top customer reviews showcase
│       ├── menu/                   # Dish details & customer review submissions
│       ├── order/                  # Customer checkout, MoMo Payment Gateway & Admin order management
│       ├── product/                # Featured dishes, paginated menu & Admin product CRUD
│       ├── reservation/            # Table booking & Admin reservation management
│       └── user/                   # Storefront layout, Admin dashboard & User CRUD
├── config/
│   ├── database.php                # Environment-driven DB configuration
│   ├── init_postgres.sql           # PostgreSQL 16 schema, PL/pgSQL triggers & seed data
│   └── dump.sql                    # Legacy MySQL dump
├── public/
│   ├── api/search.php              # JSON endpoint for live dish search
│   ├── css/                        # Modular stylesheets
│   ├── images/                     # WebP optimized dish imagery (starters & main_dishes)
│   ├── js/                         # Vanilla ES6+ scripts (Fetch API + AbortController)
│   ├── .htaccess                   # Apache rewrite rules
│   └── index.php                   # Application Front Controller
├── tests/
│   ├── bootstrap.php               # Test database bootstrapper
│   ├── CoreAndHelpersTest.php      # Core & helper unit tests
│   ├── AuthModuleTest.php          # Authentication & token security tests
│   ├── ProductMenuFeedbackTest.php # Product CRUD, pagination, sorting & review tests
│   ├── CartAndOrderTest.php        # Cart lifecycle & transactional order tests
│   └── ReservationAndAdminUserTest.php # Reservation & Admin user management tests
├── Dockerfile                      # PHP 8.2 Apache image with PostgreSQL PDO extensions
├── docker-compose.yml              # Multi-container orchestration (App + PostgreSQL 16)
├── phpunit.xml                     # PHPUnit configuration & coverage source mapping
├── composer.json                   # Dependencies & test scripts
└── README.md                       # Project documentation
```

---

## License

Copyright (c) 2026 DaTeNO Restaurant. All rights reserved.
