from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.modules.promotions import service as promotions
from tests.data import USER
from tests.integration.conftest import register_and_login
from tests.integration.test_admin_audit_api import entries, read_csv
from tests.integration.test_orders_api import OTHER_USER, checkout, fill_cart

TODAY = date(2026, 10, 30)


@pytest.fixture(autouse=True)
def frozen_calendar(monkeypatch):
    monkeypatch.setattr(promotions, "restaurant_today", lambda: TODAY)


def new_promo(admin_client, **fields):
    response = admin_client.post(
        "/api/admin/promo-codes",
        json={"code": "giam20", "kind": "PERCENT", "value": 20, **fields},
    )
    assert response.status_code == 201, response.text
    return response.json()


def check(client, code):
    return client.post("/api/promo-codes/check", json={"code": code})


@pytest.fixture
def cart_of_590k(customer, catalog):
    fill_cart(customer, catalog, pho_bo=2, beef_steak=1)  # 240,000 + 350,000
    return customer


class TestChecking:
    def test_prices_the_cart_with_a_capped_percentage_in_any_case(self, admin_client, cart_of_590k):
        new_promo(admin_client, max_discount=100_000)

        quote = check(cart_of_590k, " Giam20 ").json()

        assert quote == {
            "code": "GIAM20",
            "kind": "PERCENT",
            "value": 20,
            "subtotal": 590_000,
            "discount": 100_000,  # 20% would be 118,000
            "total": 490_000,
        }

    def test_an_amount_never_exceeds_the_dishes(self, admin_client, customer, catalog):
        new_promo(admin_client, code="TRU50K", kind="AMOUNT", value=500_000)
        fill_cart(customer, catalog, pho_bo=1)

        quote = check(customer, "tru50k").json()
        assert (quote["discount"], quote["total"]) == (120_000, 0)

    @pytest.mark.parametrize(
        ("fields", "code", "params"),
        [
            ({"starts_on": "2026-10-31"}, "promo_not_started", {"date": "2026-10-31"}),
            ({"ends_on": "2026-10-29"}, "promo_expired", {"date": "2026-10-29"}),
            ({"min_subtotal": 600_000}, "promo_min_subtotal", {"amount_vnd": 600_000}),
        ],
    )
    def test_explains_why_a_code_does_not_apply(
        self, admin_client, cart_of_590k, fields, code, params
    ):
        new_promo(admin_client, **fields)

        response = check(cart_of_590k, "GIAM20")

        assert response.status_code == 400
        assert (response.json()["code"], response.json()["params"]) == (code, params)

    def test_first_and_last_days_count(self, admin_client, cart_of_590k):
        new_promo(admin_client, starts_on=TODAY.isoformat(), ends_on=TODAY.isoformat())
        assert check(cart_of_590k, "GIAM20").status_code == 200

    def test_unknown_and_disabled_codes_look_the_same(self, admin_client, cart_of_590k):
        promo = new_promo(admin_client)
        admin_client.post(f"/api/admin/promo-codes/{promo['id']}/disable")

        for code in ("GIAM20", "NOPE"):
            response = check(cart_of_590k, code)
            assert response.status_code == 400
            assert response.json()["code"] == "promo_not_found"

    def test_needs_a_signed_in_customer_with_a_cart(self, client, customer, catalog):
        assert check(client, "GIAM20").status_code == 401
        assert check(customer, "GIAM20").json()["code"] == "cart_empty"


class TestCheckout:
    def test_the_order_keeps_subtotal_discount_and_code_and_momo_charges_the_rest(
        self, admin_client, cart_of_590k
    ):
        new_promo(admin_client)

        order = checkout(cart_of_590k, "MOMO", promo_code="giam20").json()

        assert order["subtotal_price"] == 590_000
        assert order["discount_amount"] == 118_000
        assert order["total_price"] == 472_000
        assert order["promo_code"] == "GIAM20"
        payment = cart_of_590k.post(f"/api/orders/{order['id']}/payments/momo").json()
        assert payment["amount"] == 472_000

    def test_an_order_without_a_code_pays_the_subtotal(self, cart_of_590k):
        order = checkout(cart_of_590k).json()
        assert (order["subtotal_price"], order["discount_amount"], order["total_price"]) == (
            590_000,
            0,
            590_000,
        )
        assert order["promo_code"] is None

    def test_a_refused_code_places_no_order_and_keeps_the_cart(self, admin_client, cart_of_590k):
        response = checkout(cart_of_590k, promo_code="NOPE")

        assert response.status_code == 400
        assert cart_of_590k.get("/api/orders").json() == []
        assert cart_of_590k.get("/api/cart").json()["total_count"] == 3

    def test_each_customer_may_use_it_once_until_they_cancel(self, admin_client, customer, catalog):
        new_promo(admin_client)
        fill_cart(customer, catalog, pho_bo=1)
        first = checkout(customer, promo_code="GIAM20").json()

        fill_cart(customer, catalog, pho_bo=1)
        again = checkout(customer, promo_code="GIAM20")
        assert again.status_code == 400
        assert again.json()["code"] == "promo_already_used"

        customer.post(f"/api/orders/{first['id']}/cancel")
        assert checkout(customer, promo_code="GIAM20").status_code == 201

    def test_a_limited_code_runs_out_across_customers(
        self, admin_client, customer, client, catalog
    ):
        new_promo(admin_client, usage_limit=1, per_customer_limit=None)
        fill_cart(customer, catalog, pho_bo=1)
        assert checkout(customer, promo_code="GIAM20").status_code == 201

        client.post("/api/auth/logout")
        register_and_login(client, OTHER_USER)
        fill_cart(client, catalog, pho_bo=1)
        response = checkout(client, promo_code="GIAM20")
        assert response.json()["code"] == "promo_used_up"

    def test_the_email_shows_the_discount(self, admin_client, cart_of_590k, outbox):
        new_promo(admin_client)
        checkout(cart_of_590k, promo_code="GIAM20")

        email = outbox.sent[-1]
        assert "Tạm tính: 590.000 ₫" in email.text
        assert "Giảm giá (GIAM20): -118.000 ₫" in email.text
        assert "Total: 472.000 ₫" in email.text


class TestReorder:
    def test_puts_the_dishes_back_on_top_of_the_cart_at_todays_prices(self, customer, catalog, db):
        fill_cart(customer, catalog, pho_bo=2, beef_steak=1)
        order_id = checkout(customer).json()["id"]
        fill_cart(customer, catalog, pho_bo=1)
        catalog.products["pho-bo"].price = 130_000
        db.commit()

        result = customer.post(f"/api/orders/{order_id}/reorder").json()

        assert (result["added"], result["skipped"]) == (2, [])
        lines = {line["product"]["slug"]: line for line in result["cart"]["items"]}
        assert lines["pho-bo"]["quantity"] == 3
        assert lines["pho-bo"]["subtotal"] == 390_000
        assert lines["beef-steak"]["quantity"] == 1

    def test_skips_dishes_no_longer_on_the_menu(self, customer, catalog, db):
        fill_cart(customer, catalog, pho_bo=1, beef_steak=1)
        order_id = checkout(customer).json()["id"]
        hidden = catalog.products["beef-steak"]
        hidden.deleted_at = hidden.created_at
        db.commit()

        result = customer.post(f"/api/orders/{order_id}/reorder").json()

        assert result["added"] == 1
        assert result["skipped"] == [{"vi": "Bò bít tết", "en": "Beef Steak"}]
        assert [line["product"]["slug"] for line in result["cart"]["items"]] == ["pho-bo"]

    def test_only_your_own_orders(self, client, customer, catalog):
        fill_cart(customer, catalog, pho_bo=1)
        order_id = checkout(customer).json()["id"]

        register_and_login(client, OTHER_USER)
        response = client.post(f"/api/orders/{order_id}/reorder")
        assert response.status_code == 404


class TestAdmin:
    def test_lists_codes_with_their_live_uses(self, admin_client, customer, catalog):
        new_promo(admin_client, code="OLD")
        promo = new_promo(admin_client)
        fill_cart(customer, catalog, pho_bo=1)
        checkout(customer, promo_code="GIAM20")
        admin_client.post(f"/api/admin/promo-codes/{promo['id'] - 1}/disable")

        listed = admin_client.get("/api/admin/promo-codes").json()

        assert [(p["code"], p["uses"], p["disabled_at"] is None) for p in listed] == [
            ("GIAM20", 1, True),
            ("OLD", 0, False),
        ]

    def test_codes_are_unique_whatever_the_case(self, admin_client):
        new_promo(admin_client)
        response = admin_client.post(
            "/api/admin/promo-codes", json={"code": "Giam20", "kind": "AMOUNT", "value": 10_000}
        )
        assert response.status_code == 409
        assert response.json()["code"] == "promo_code_taken"

    @pytest.mark.parametrize(
        "fields",
        [
            {"kind": "PERCENT", "value": 101},
            {"kind": "AMOUNT", "value": 500},
            {"code": "có dấu"},
            {"code": "AB"},
            {"starts_on": "2026-11-05", "ends_on": "2026-11-01"},
        ],
    )
    def test_rejects_inconsistent_codes(self, admin_client, fields):
        response = admin_client.post(
            "/api/admin/promo-codes",
            json={"code": "GIAM20", "kind": "PERCENT", "value": 20, **fields},
        )
        assert response.status_code == 422

    def test_an_amount_has_no_cap(self, admin_client):
        promo = new_promo(admin_client, kind="AMOUNT", value=30_000, max_discount=10_000)
        assert promo["max_discount"] is None

    def test_edits_and_switches_are_logged(self, admin_client):
        promo = new_promo(admin_client)
        updated = admin_client.put(
            f"/api/admin/promo-codes/{promo['id']}",
            json={"code": "GIAM25", "kind": "PERCENT", "value": 25, "ends_on": "2026-11-30"},
        ).json()
        admin_client.post(f"/api/admin/promo-codes/{promo['id']}/disable")
        admin_client.post(f"/api/admin/promo-codes/{promo['id']}/disable")  # already off
        admin_client.post(f"/api/admin/promo-codes/{promo['id']}/enable")

        assert updated["code"] == "GIAM25"
        log = entries(admin_client, action="promo")
        assert [entry["action"] for entry in log] == [
            "promo.enable",
            "promo.disable",
            "promo.update",
            "promo.create",
        ]
        assert log[2]["changes"] == {
            "code": ["GIAM20", "GIAM25"],
            "value": [20, 25],
            "ends_on": [None, "2026-11-30"],
        }

    def test_unknown_code(self, admin_client):
        response = admin_client.post("/api/admin/promo-codes/999/disable")
        assert response.status_code == 404

    def test_customers_cannot_manage_codes(self, customer):
        assert customer.get("/api/admin/promo-codes").status_code == 403


def test_exports_show_the_discount(admin_client, customer, catalog):
    new_promo(admin_client)
    fill_cart(customer, catalog, pho_bo=1)
    checkout(customer, promo_code="GIAM20")

    today = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat()
    rows = read_csv(admin_client.get(f"/api/admin/exports/orders.csv?from={today}&to={today}"))
    assert rows[0][-2:] == ["Giảm giá (VND)", "Mã giảm giá"]
    assert rows[1][-2:] == ["24000", "GIAM20"]
    assert USER["email"] in rows[1]
