"""The desserts-and-drinks migration (5c2e8a91d7f3) undone and redone on a real database."""

from collections.abc import Iterator

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine, event, text

from alembic import command
from app.core.config import BACKEND_DIR

MENU = "5c2e8a91d7f3"
BEFORE = "30b9ab2e6605"
ORDERED = "sugarcane-kumquat-juice"


@pytest.fixture
def database(tmp_path) -> Iterator[tuple[Config, Engine]]:
    url = f"sqlite:///{tmp_path / 'menu.db'}"
    engine = create_engine(url)

    # SQLite only enforces foreign keys when asked, on every connection, Alembic's included.
    def enforce(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    event.listen(Engine, "connect", enforce)
    # No ini file: env.py would apply its logging config and silence loggers other tests read.
    config = Config()
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    try:
        command.upgrade(config, MENU)
        yield config, engine
    finally:
        event.remove(Engine, "connect", enforce)
        engine.dispose()


def order_one(engine: Engine, slug: str) -> None:
    with engine.begin() as conn:
        user = conn.execute(
            text(
                "INSERT INTO users (name, email, password_hash, role, phone, search_text) "
                "VALUES ('Khach', 'k@example.com', '!', 'CUSTOMER', '0900000001', 'khach') "
                "RETURNING id"
            )
        ).scalar_one()
        order = conn.execute(
            text(
                "INSERT INTO orders (user_id, status, payment_method, payment_status, "
                "subtotal_price, discount_amount, total_price, delivery_name, delivery_phone, "
                "delivery_address, delivery_note) VALUES (:user, 'COMPLETED', 'COD', 'PAID', "
                "1, 0, 1, 'Khach', '0900000001', '1 Le Loi', '') RETURNING id"
            ),
            {"user": user},
        ).scalar_one()
        conn.execute(
            text(
                "INSERT INTO order_items (order_id, product_id, price_at_purchase, quantity) "
                "SELECT :order, id, price, 1 FROM products WHERE slug = :slug"
            ),
            {"order": order, "slug": slug},
        )


def rows(engine: Engine, sql: str) -> list[tuple]:
    with engine.connect() as conn:
        return [tuple(row) for row in conn.execute(text(sql))]


def test_undoing_keeps_ordered_dishes_hidden_and_removes_the_rest(database):
    config, engine = database
    order_one(engine, ORDERED)

    command.downgrade(config, BEFORE)

    # The ordered drink stays, hidden, in its hidden category; the order keeps its line.
    assert rows(
        engine,
        "SELECT p.slug, p.deleted_at IS NOT NULL, c.slug, c.deleted_at IS NOT NULL "
        "FROM products p JOIN categories c ON c.id = p.category_id "
        "WHERE c.slug IN ('desserts', 'drinks')",
    ) == [(ORDERED, 1, "drinks", 1)]
    assert rows(engine, "SELECT count(*) FROM order_items") == [(1,)]
    # Desserts held nothing ordered, so the category is gone; the original menu is untouched.
    assert rows(engine, "SELECT slug FROM categories ORDER BY id") == [
        ("starters",),
        ("main_dishes",),
        ("drinks",),
    ]
    assert rows(engine, "SELECT count(*) FROM products WHERE deleted_at IS NULL") == [(30,)]


def test_redoing_shows_the_kept_dishes_again_without_duplicates(database):
    config, engine = database
    order_one(engine, ORDERED)
    command.downgrade(config, BEFORE)

    command.upgrade(config, MENU)

    assert rows(engine, "SELECT count(*), count(deleted_at) FROM products") == [(60, 0)]
    assert rows(engine, "SELECT count(*), count(deleted_at) FROM categories") == [(4, 0)]
    # The kept drink was not inserted twice and still has its branches.
    assert rows(
        engine,
        "SELECT count(DISTINCT pa.location_id) FROM products p "
        f"JOIN product_availabilities pa ON pa.product_id = p.id WHERE p.slug = '{ORDERED}'",
    ) == rows(engine, "SELECT count(*) FROM locations")


def test_undoing_an_unordered_menu_removes_it_all(database):
    config, engine = database

    command.downgrade(config, BEFORE)

    assert rows(engine, "SELECT count(*) FROM products") == [(30,)]
    assert rows(engine, "SELECT slug FROM categories ORDER BY id") == [
        ("starters",),
        ("main_dishes",),
    ]
