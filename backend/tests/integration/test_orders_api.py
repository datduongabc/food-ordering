from decimal import Decimal

import pytest

from app.core.config import get_settings
from app.core.db import utcnow
from app.modules.catalog.models import Product
from tests.data import USER
from tests.integration.conftest import register_and_login

OTHER_USER = {**USER, "email": "other@example.com", "phone": "0922222222"}


@pytest.fixture
def shopper(client, catalog):
    register_and_login(client, USER)
    return client


def fill_cart(client, catalog, **quantities):
    for slug, quantity in quantities.items():
        product_id = catalog.products[slug.replace("_", "-")].id
        client.post("/api/cart/items", json={"product_id": product_id, "quantity": quantity})


def checkout(client, payment_method="COD"):
    return client.post("/api/orders", json={"payment_method": payment_method})


class TestCheckout:
    def test_creates_pending_order_with_snapshot_prices_and_clears_cart(self, shopper, catalog, db):
        fill_cart(shopper, catalog, pho_bo=2, beef_steak=1)

        response = checkout(shopper)

        assert response.status_code == 201
        order = response.json()
        assert order["status"] == "PENDING"
        assert order["payment_method"] == "COD"
        assert order["payment_status"] == "UNPAID"
        assert order["total_price"] == "59.00"
        assert order["can_cancel"] is True
        assert [(i["product_slug"], i["quantity"], i["subtotal"]) for i in order["items"]] == [
            ("pho-bo", 2, "24.00"),
            ("beef-steak", 1, "35.00"),
        ]
        assert order["items"][0]["image_url"] == "/media/products/main_dishes/pho-bo.webp"
        assert shopper.get("/api/cart").json()["items"] == []

        # A later menu price change must not rewrite what the customer was charged.
        db.get(Product, catalog.products["pho-bo"].id).price = Decimal("99.00")
        db.commit()
        again = shopper.get(f"/api/orders/{order['id']}").json()
        assert again["total_price"] == "59.00"
        assert again["items"][0]["price_at_purchase"] == "12.00"

    def test_empty_cart_is_rejected(self, shopper):
        response = checkout(shopper)

        assert response.status_code == 400
        assert "cart is empty" in response.json()["detail"]

    def test_second_submit_finds_empty_cart(self, shopper, catalog):
        fill_cart(shopper, catalog, pho_bo=1)

        assert checkout(shopper).status_code == 201
        assert checkout(shopper).status_code == 400
        assert len(shopper.get("/api/orders").json()) == 1

    def test_skips_dishes_removed_from_menu(self, shopper, catalog, db):
        fill_cart(shopper, catalog, pho_bo=1, beef_steak=1)
        db.get(Product, catalog.products["beef-steak"].id).deleted_at = utcnow()
        db.commit()

        order = checkout(shopper).json()

        assert [i["product_slug"] for i in order["items"]] == ["pho-bo"]
        assert order["total_price"] == "12.00"

    def test_rejects_unknown_payment_method(self, shopper, catalog):
        fill_cart(shopper, catalog, pho_bo=1)
        assert checkout(shopper, "BITCOIN").status_code == 422

    def test_requires_sign_in(self, client):
        assert checkout(client).status_code == 401


class TestViewingOrders:
    def test_lists_newest_first(self, shopper, catalog):
        fill_cart(shopper, catalog, pho_bo=1)
        first = checkout(shopper).json()["id"]
        fill_cart(shopper, catalog, beef_steak=1)
        second = checkout(shopper).json()["id"]

        assert [o["id"] for o in shopper.get("/api/orders").json()] == [second, first]

    def test_other_customers_orders_are_invisible(self, client, catalog):
        register_and_login(client, USER)
        fill_cart(client, catalog, pho_bo=1)
        order_id = checkout(client).json()["id"]
        client.post("/api/auth/logout")
        register_and_login(client, OTHER_USER)

        assert client.get("/api/orders").json() == []
        assert client.get(f"/api/orders/{order_id}").status_code == 404
        assert client.post(f"/api/orders/{order_id}/cancel").status_code == 404
        assert client.post(f"/api/orders/{order_id}/payments/momo").status_code == 404


class TestCancel:
    def test_cancels_pending_order_once(self, shopper, catalog):
        fill_cart(shopper, catalog, pho_bo=1)
        order_id = checkout(shopper).json()["id"]

        cancelled = shopper.post(f"/api/orders/{order_id}/cancel")
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "CANCELLED"
        assert cancelled.json()["can_cancel"] is False

        again = shopper.post(f"/api/orders/{order_id}/cancel")
        assert again.status_code == 409


class TestMomoSandbox:
    @pytest.fixture
    def order_id(self, shopper, catalog) -> int:
        fill_cart(shopper, catalog, pho_bo=2, beef_steak=1)  # $59.00
        return checkout(shopper, "MOMO").json()["id"]

    def start(self, client, order_id):
        return client.post(f"/api/orders/{order_id}/payments/momo")

    def complete(self, client, momo_order_id, result):
        return client.post(
            "/api/payments/momo/sandbox/complete",
            json={"momo_order_id": momo_order_id, "result": result},
        )

    def test_start_converts_total_to_vnd(self, shopper, order_id):
        response = self.start(shopper, order_id)

        assert response.status_code == 200
        body = response.json()
        assert body["amount_usd"] == "59.00"
        assert body["amount_vnd"] == 1_475_000
        assert body["exchange_rate"] == 25_000
        assert body["mode"] == "sandbox"
        assert body["momo_order_id"].startswith(f"DATENO_{order_id}_")

    def test_approval_marks_paid_and_confirms(self, shopper, order_id):
        momo_order_id = self.start(shopper, order_id).json()["momo_order_id"]

        response = self.complete(shopper, momo_order_id, "approved")

        order = response.json()
        assert response.status_code == 200
        assert (order["status"], order["payment_status"]) == ("CONFIRMED", "PAID")
        assert order["can_pay"] is False and order["can_cancel"] is False
        assert self.start(shopper, order_id).status_code == 409
        assert self.complete(shopper, momo_order_id, "approved").status_code == 409

    def test_decline_then_retry_with_new_payment_id(self, shopper, order_id):
        first = self.start(shopper, order_id).json()["momo_order_id"]
        declined = self.complete(shopper, first, "declined").json()
        assert (declined["status"], declined["payment_status"]) == ("PENDING", "FAILED")
        assert declined["can_pay"] is True

        second = self.start(shopper, order_id).json()["momo_order_id"]
        assert second != first
        # The old attempt id is dead once a new one is issued.
        assert self.complete(shopper, first, "approved").status_code == 404
        assert self.complete(shopper, second, "approved").json()["payment_status"] == "PAID"

    def test_cancelled_order_cannot_be_paid(self, shopper, order_id):
        momo_order_id = self.start(shopper, order_id).json()["momo_order_id"]
        shopper.post(f"/api/orders/{order_id}/cancel")

        assert self.start(shopper, order_id).status_code == 409
        assert self.complete(shopper, momo_order_id, "approved").status_code == 409

    def test_cod_order_can_switch_to_momo(self, shopper, catalog):
        fill_cart(shopper, catalog, pho_bo=1)
        order_id = checkout(shopper, "COD").json()["id"]

        self.start(shopper, order_id)

        assert shopper.get(f"/api/orders/{order_id}").json()["payment_method"] == "MOMO"

    def test_amount_outside_momo_limits_is_refused_not_clamped(self, shopper, catalog, db):
        db.get(Product, catalog.products["pho-bo"].id).price = Decimal("0.01")
        db.commit()
        fill_cart(shopper, catalog, pho_bo=1)  # 250 VND, below MoMo's 1,000 VND minimum
        order_id = checkout(shopper, "MOMO").json()["id"]

        response = self.start(shopper, order_id)

        assert response.status_code == 400
        assert "1,000-50,000,000 VND" in response.json()["detail"]

    def test_unavailable_outside_local_mode(self, shopper, order_id, monkeypatch):
        momo_order_id = self.start(shopper, order_id).json()["momo_order_id"]
        monkeypatch.setattr(get_settings(), "app_env", "production")

        assert self.start(shopper, order_id).status_code == 503
        assert self.complete(shopper, momo_order_id, "approved").status_code == 503
