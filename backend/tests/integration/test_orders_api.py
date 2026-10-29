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


def delivery(client, branch="District 7", **overrides) -> dict:
    location_id = next(
        loc["id"] for loc in client.get("/api/locations").json() if loc["name"]["en"] == branch
    )
    return {
        "location_id": location_id,
        "delivery_name": "Nguyen Van A",
        "delivery_phone": "0901234567",
        "delivery_address": "12 Nguyen Hue, District 1, Ho Chi Minh City",
        **overrides,
    }


def checkout(client, payment_method="COD", **overrides):
    return client.post(
        "/api/orders", json={"payment_method": payment_method, **delivery(client, **overrides)}
    )


class TestCheckout:
    def test_creates_pending_order_with_snapshot_prices_and_clears_cart(self, shopper, catalog, db):
        fill_cart(shopper, catalog, pho_bo=2, beef_steak=1)

        response = checkout(shopper)

        assert response.status_code == 201
        order = response.json()
        assert order["status"] == "PENDING"
        assert order["payment_method"] == "COD"
        assert order["payment_status"] == "UNPAID"
        assert order["total_price"] == 590_000
        assert order["can_cancel"] is True
        assert [(i["product_slug"], i["quantity"], i["subtotal"]) for i in order["items"]] == [
            ("pho-bo", 2, 240_000),
            ("beef-steak", 1, 350_000),
        ]
        assert order["items"][0]["image_url"] == "/media/products/main_dishes/pho-bo.webp"
        assert shopper.get("/api/cart").json()["items"] == []

        # A later menu price change must not rewrite what the customer was charged.
        db.get(Product, catalog.products["pho-bo"].id).price = 990_000
        db.commit()
        again = shopper.get(f"/api/orders/{order['id']}").json()
        assert again["total_price"] == 590_000
        assert again["items"][0]["price_at_purchase"] == 120_000

    def test_empty_cart_is_rejected(self, shopper):
        response = checkout(shopper)

        assert response.status_code == 400
        assert response.json()["code"] == "cart_empty"

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
        assert order["total_price"] == 120_000

    def test_rejects_unknown_payment_method(self, shopper, catalog):
        fill_cart(shopper, catalog, pho_bo=1)
        assert checkout(shopper, "BITCOIN").status_code == 422

    def test_requires_sign_in(self, client, catalog):
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

    def test_start_charges_the_order_total(self, shopper, order_id):
        response = self.start(shopper, order_id)

        assert response.status_code == 200
        body = response.json()
        assert body["amount"] == 590_000
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
        db.get(Product, catalog.products["pho-bo"].id).price = 500
        db.commit()
        fill_cart(shopper, catalog, pho_bo=1)  # 500 VND, below MoMo's 1,000 VND minimum
        order_id = checkout(shopper, "MOMO").json()["id"]

        response = self.start(shopper, order_id)

        assert response.status_code == 400
        assert response.json()["code"] == "momo_amount_out_of_range"
        assert response.json()["params"] == {"min_vnd": 1_000, "max_vnd": 50_000_000}

    def test_unavailable_outside_local_mode(self, shopper, order_id, monkeypatch):
        momo_order_id = self.start(shopper, order_id).json()["momo_order_id"]
        monkeypatch.setattr(get_settings(), "app_env", "production")

        assert self.start(shopper, order_id).status_code == 503
        assert self.complete(shopper, momo_order_id, "approved").status_code == 503


class TestDeliveryDetails:
    def test_checkout_stores_delivery_details_and_history(self, shopper, catalog):
        fill_cart(shopper, catalog, beef_steak=1)

        order = checkout(shopper, branch="District 1", delivery_note="  Ring twice  ").json()

        assert order["location"]["name"]["en"] == "District 1"
        assert order["delivery_name"] == "Nguyen Van A"
        assert order["delivery_phone"] == "0901234567"
        assert order["delivery_address"] == "12 Nguyen Hue, District 1, Ho Chi Minh City"
        assert order["delivery_note"] == "Ring twice"
        assert [(e["from_status"], e["to_status"]) for e in order["events"]] == [(None, "PENDING")]

    def test_rejects_dishes_not_served_by_the_branch(self, shopper, catalog):
        # Spring rolls are only made in District 1; pho only in District 7.
        fill_cart(shopper, catalog, spring_rolls=1, pho_bo=1)

        response = checkout(shopper, branch="District 7")

        assert response.status_code == 400
        assert response.json()["code"] == "dishes_unavailable_at_branch"
        assert response.json()["params"] == {
            "branch": {"vi": "Quận 7", "en": "District 7"},
            "dishes": [{"vi": "Gỏi cuốn tôm", "en": "Shrimp Spring Rolls"}],
        }
        assert shopper.get("/api/cart").json()["total_count"] == 2  # cart left untouched

    def test_unknown_branch(self, shopper, catalog):
        fill_cart(shopper, catalog, pho_bo=1)
        response = shopper.post(
            "/api/orders", json={**delivery(shopper), "location_id": 999, "payment_method": "COD"}
        )
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "overrides",
        [
            {"delivery_address": "  "},
            {"delivery_address": "abc"},
            {"delivery_phone": "123"},
            {"delivery_name": ""},
            {"delivery_note": "x" * 501},
        ],
    )
    def test_validates_delivery_fields(self, shopper, catalog, overrides):
        fill_cart(shopper, catalog, pho_bo=1)
        assert checkout(shopper, **overrides).status_code == 422

    def test_history_records_customer_cancel_and_momo_confirmation(self, shopper, catalog):
        fill_cart(shopper, catalog, pho_bo=1)
        cancelled = shopper.post(f"/api/orders/{checkout(shopper).json()['id']}/cancel").json()
        assert [(e["to_status"], e["note"]) for e in cancelled["events"]] == [
            ("PENDING", ""),
            ("CANCELLED", "Cancelled by customer."),
        ]

        fill_cart(shopper, catalog, pho_bo=1)
        order_id = checkout(shopper, "MOMO").json()["id"]
        momo_id = shopper.post(f"/api/orders/{order_id}/payments/momo").json()["momo_order_id"]
        paid = shopper.post(
            "/api/payments/momo/sandbox/complete",
            json={"momo_order_id": momo_id, "result": "approved"},
        ).json()
        assert paid["events"][-1]["from_status"] == "PENDING"
        assert paid["events"][-1]["to_status"] == "CONFIRMED"
        assert paid["events"][-1]["note"] == "MoMo payment received."
        assert "actor_name" not in paid["events"][-1]  # staff identities stay internal
