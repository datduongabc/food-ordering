import re
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registers every table on Base.metadata)
from app.core.config import get_settings
from app.core.db import Base, get_db, utcnow
from app.core.email import Email, get_email_sender
from app.core.security import hash_password
from app.main import create_app
from app.modules.catalog.models import Category, Location, Product
from app.modules.users.models import Role, User
from tests.conftest import TEST_DATABASE_URL
from tests.data import USER


class Outbox:
    def __init__(self) -> None:
        self.sent: list[Email] = []

    def send(self, email: Email) -> None:
        self.sent.append(email)

    def last_code(self) -> str:
        match = re.search(r"\b(\d{6})\b", self.sent[-1].text)
        assert match, "no 6-digit code in the last email"
        return match.group(1)


@pytest.fixture(scope="session")
def postgres_engine() -> Iterator[Engine]:
    # Schema is built once per run; each test then truncates, which is far cheaper than DDL.
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session_factory(request) -> Iterator[sessionmaker[Session]]:
    if TEST_DATABASE_URL.startswith("postgresql"):
        engine = request.getfixturevalue("postgres_engine")
        yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
        return

    # StaticPool shares one in-memory connection, so the app and the test see the same data.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def db(db_session_factory) -> Iterator[Session]:
    with db_session_factory() as session:
        yield session


@pytest.fixture
def outbox() -> Outbox:
    return Outbox()


@pytest.fixture(autouse=True)
def media_dir(tmp_path, monkeypatch) -> Path:
    """Uploads go to a per-test folder, never into the repository's media directory."""
    path = tmp_path / "media"
    (path / "products").mkdir(parents=True)
    monkeypatch.setattr(get_settings(), "media_dir", path)
    return path


@pytest.fixture
def client(db_session_factory, outbox) -> Iterator[TestClient]:
    app = create_app()

    def override_get_db() -> Iterator[Session]:
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_email_sender] = lambda: outbox

    with TestClient(app) as test_client:
        # Mirror the SPA: fetch the CSRF cookie once, then echo it on every request.
        test_client.get("/api/health")
        test_client.headers["X-CSRF-Token"] = test_client.cookies[get_settings().csrf_cookie_name]
        yield test_client


@dataclass
class Catalog:
    starters: Category
    mains: Category
    district1: Location
    district7: Location
    products: dict[str, Product]


@pytest.fixture
def catalog(db) -> Catalog:
    """Five dishes chosen to make ordering observable; ids follow insertion order."""
    starters = Category(name={"vi": "Khai vị", "en": "Starters"}, slug="starters")
    mains = Category(name={"vi": "Món chính", "en": "Main Dishes"}, slug="main_dishes")
    district1 = Location(
        name={"vi": "Quận 1", "en": "District 1"},
        address={"vi": "1 Lê Lợi", "en": "1 Le Loi"},
    )
    district7 = Location(
        name={"vi": "Quận 7", "en": "District 7"},
        address={"vi": "7 Nguyễn Văn Linh", "en": "7 Nguyen Van Linh"},
    )
    db.add_all([starters, mains, district1, district7])
    db.flush()

    def dish(slug, names, category, price, rating=None, locations=(), deleted=False):
        name_vi, name_en = names
        return Product(
            slug=slug,
            name={"vi": name_vi, "en": name_en},
            description={"vi": f"Mô tả {name_vi}", "en": f"{name_en} description"},
            category=category,
            image_url=f"{category.slug}/{slug}.webp",
            price=price,
            average_rating=Decimal(rating) if rating else None,
            locations=list(locations),
            deleted_at=utcnow() if deleted else None,
        )

    products = {
        p.slug: p
        for p in [
            dish(
                "spring-rolls",
                ("Gỏi cuốn tôm", "Shrimp Spring Rolls"),
                starters,
                95_000,
                "4.00",
                [district1],
            ),
            dish("garlic-bread", ("Bánh mì bơ tỏi", "Garlic Butter Bread"), starters, 60_000),
            dish(
                "beef-steak",
                ("Bò bít tết", "Beef Steak"),
                mains,
                350_000,
                "5.00",
                [district1, district7],
            ),
            dish("pho-bo", ("Phở bò", "Pho Bo"), mains, 120_000, "3.50", [district7]),
            dish(
                "old-dish",
                ("Món xuân cũ", "Retired Spring Special"),
                starters,
                10_000,
                "5.00",
                deleted=True,
            ),
        ]
    }
    db.add_all(products.values())
    db.commit()
    return Catalog(starters, mains, district1, district7, products)


def register_and_login(client: TestClient, user: dict) -> None:
    assert client.post("/api/auth/register", json=user).status_code == 201
    login = client.post(
        "/api/auth/login", json={"email": user["email"], "password": user["password"]}
    )
    assert login.status_code == 200, login.text


@pytest.fixture
def shopper(client, catalog):
    register_and_login(client, USER)
    return client


@pytest.fixture
def customer(second_client, catalog):
    """A signed-in customer in a separate browser from the admin."""
    register_and_login(second_client, USER)
    return second_client


ADMIN = {
    "name": "Quan Ly",
    "email": "admin@dateno.vn",
    "password": "admin-password",
    "phone": "0819152362",
}


@pytest.fixture
def admin_client(client, db) -> TestClient:
    db.add(
        User(
            name=ADMIN["name"],
            email=ADMIN["email"],
            phone=ADMIN["phone"],
            password_hash=hash_password(ADMIN["password"]),
            role=Role.ADMIN,
        )
    )
    db.commit()
    response = client.post(
        "/api/auth/login", json={"email": ADMIN["email"], "password": ADMIN["password"]}
    )
    assert response.status_code == 200, response.text
    return client


@pytest.fixture
def second_client(client) -> Iterator[TestClient]:
    """Another browser on the same app and database, e.g. a customer while an admin acts."""
    with TestClient(client.app) as other:
        other.get("/api/health")
        other.headers["X-CSRF-Token"] = other.cookies[get_settings().csrf_cookie_name]
        yield other


@pytest.fixture
def registered_user(client) -> dict:
    response = client.post("/api/auth/register", json=USER)
    assert response.status_code == 201, response.text
    return USER


@pytest.fixture
def logged_in_client(client, registered_user) -> TestClient:
    response = client.post(
        "/api/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert response.status_code == 200, response.text
    return client
