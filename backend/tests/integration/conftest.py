import re
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registers every table on Base.metadata)
from app.core.config import get_settings
from app.core.db import Base, get_db
from app.core.email import Email, get_email_sender
from app.main import create_app
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
