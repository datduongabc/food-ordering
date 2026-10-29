"""Guest cart, sign-in merge, checkout and MoMo sandbox payment against a real server."""

import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from tests.conftest import TEST_DATABASE_URL


def new_customer() -> dict:
    suffix = uuid.uuid4().hex[:8]
    return {
        "name": "Hoang Thi E",
        "email": f"e-{suffix}@example.com",
        "password": "shopping-password",
        "phone": f"07{int(suffix, 16) % 10**8:08d}",
    }


def sign_up_and_in(browser, customer: dict) -> None:
    browser.post("/api/auth/register", json=customer).raise_for_status()
    browser.post(
        "/api/auth/login", json={"email": customer["email"], "password": customer["password"]}
    ).raise_for_status()


def product_id(browser, slug: str) -> int:
    return browser.get(f"/api/products/{slug}").json()["id"]


def test_guest_cart_merges_then_pays_with_momo_after_a_decline(new_browser):
    browser = new_browser()
    pho, prawns = (
        product_id(browser, "royal-seafood-fried-rice"),
        product_id(browser, "coconut-steamed-prawns"),
    )

    # Guest: the cart lives in the browser; the server only prices it.
    guest_cart = {
        "items": [{"product_id": pho, "quantity": 2}, {"product_id": prawns, "quantity": 1}]
    }
    preview = browser.post("/api/cart/preview", json=guest_cart).json()
    assert preview["total_price"] == "58.00"  # 2 x 16.50 + 25.00

    sign_up_and_in(browser, new_customer())
    merged = browser.post("/api/cart/merge", json=guest_cart).json()
    assert merged["total_price"] == "58.00"

    order = browser.post("/api/orders", json={"payment_method": "MOMO"}).json()
    assert order["status"] == "PENDING"
    assert browser.get("/api/cart").json()["total_count"] == 0

    first = browser.post(f"/api/orders/{order['id']}/payments/momo").json()
    assert first["amount_vnd"] == 1_450_000
    declined = browser.post(
        "/api/payments/momo/sandbox/complete",
        json={"momo_order_id": first["momo_order_id"], "result": "declined"},
    ).json()
    assert declined["payment_status"] == "FAILED"

    retry = browser.post(f"/api/orders/{order['id']}/payments/momo").json()
    paid = browser.post(
        "/api/payments/momo/sandbox/complete",
        json={"momo_order_id": retry["momo_order_id"], "result": "approved"},
    ).json()
    assert (paid["status"], paid["payment_status"]) == ("CONFIRMED", "PAID")

    history = browser.get("/api/orders").json()
    assert [(o["id"], o["payment_status"]) for o in history] == [(order["id"], "PAID")]


def test_cash_on_delivery_order_can_be_cancelled(new_browser):
    browser = new_browser()
    sign_up_and_in(browser, new_customer())
    browser.post(
        "/api/cart/items", json={"product_id": product_id(browser, "caesar-salad"), "quantity": 1}
    ).raise_for_status()

    order = browser.post("/api/orders", json={"payment_method": "COD"}).json()
    cancelled = browser.post(f"/api/orders/{order['id']}/cancel").json()

    assert cancelled["status"] == "CANCELLED"
    assert browser.post(f"/api/orders/{order['id']}/payments/momo").status_code == 409


@pytest.mark.skipif(
    not TEST_DATABASE_URL.startswith("postgresql"),
    reason="needs Postgres row locks; SQLite serialises writers differently",
)
def test_simultaneous_checkouts_create_exactly_one_order(new_browser):
    browser = new_browser()
    sign_up_and_in(browser, new_customer())
    browser.post(
        "/api/cart/items",
        json={"product_id": product_id(browser, "peking-roast-duck"), "quantity": 1},
    ).raise_for_status()

    # Separate connections sharing the signed-in cookies, like a frantic double/triple click.
    tabs = [new_browser() for _ in range(8)]
    for tab in tabs:
        tab.cookies.update(browser.cookies)
        tab.headers["X-CSRF-Token"] = browser.headers["X-CSRF-Token"]

    with ThreadPoolExecutor(max_workers=len(tabs)) as pool:
        statuses = sorted(
            pool.map(
                lambda tab: tab.post("/api/orders", json={"payment_method": "COD"}).status_code,
                tabs,
            )
        )

    assert statuses == [201] + [400] * 7
    assert len(browser.get("/api/orders").json()) == 1
