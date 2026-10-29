import pytest

from app.core.db import utcnow
from tests.data import USER
from tests.integration.conftest import register_and_login


def lines(cart: dict) -> list[tuple[str, int]]:
    return [(item["product"]["slug"], item["quantity"]) for item in cart["items"]]


@pytest.fixture
def shopper(client, catalog):
    register_and_login(client, USER)
    return client


def add(client, product, quantity=1):
    return client.post("/api/cart/items", json={"product_id": product.id, "quantity": quantity})


class TestMemberCart:
    def test_requires_sign_in(self, client, catalog):
        assert client.get("/api/cart").status_code == 401
        assert add(client, catalog.products["pho-bo"]).status_code == 401

    def test_starts_empty(self, shopper):
        assert shopper.get("/api/cart").json() == {
            "items": [],
            "total_count": 0,
            "total_price": "0.00",
        }

    def test_add_increments_and_totals(self, shopper, catalog):
        pho, steak = catalog.products["pho-bo"], catalog.products["beef-steak"]
        add(shopper, pho, 2)
        add(shopper, steak)
        response = add(shopper, pho)

        cart = response.json()
        assert response.status_code == 200
        assert lines(cart) == [("pho-bo", 3), ("beef-steak", 1)]
        assert cart["items"][0]["subtotal"] == "36.00"
        assert cart["total_count"] == 4
        assert cart["total_price"] == "71.00"

    def test_quantity_is_capped_at_99(self, shopper, catalog):
        add(shopper, catalog.products["pho-bo"], 60)
        assert lines(add(shopper, catalog.products["pho-bo"], 60).json()) == [("pho-bo", 99)]

    @pytest.mark.parametrize("quantity", [0, -1, 100])
    def test_rejects_out_of_range_quantity(self, shopper, catalog, quantity):
        assert add(shopper, catalog.products["pho-bo"], quantity).status_code == 422

    @pytest.mark.parametrize("slug", ["old-dish", None])
    def test_cannot_add_deleted_or_unknown_dish(self, shopper, catalog, slug):
        product_id = catalog.products[slug].id if slug else 999_999
        response = shopper.post("/api/cart/items", json={"product_id": product_id})
        assert response.status_code == 404

    def test_set_quantity_and_remove(self, shopper, catalog):
        pho, steak = catalog.products["pho-bo"], catalog.products["beef-steak"]
        add(shopper, pho)
        add(shopper, steak)

        updated = shopper.put(f"/api/cart/items/{pho.id}", json={"quantity": 5}).json()
        assert lines(updated) == [("pho-bo", 5), ("beef-steak", 1)]

        removed = shopper.delete(f"/api/cart/items/{steak.id}").json()
        assert lines(removed) == [("pho-bo", 5)]

    def test_set_quantity_of_missing_line_is_404(self, shopper, catalog):
        pho = catalog.products["pho-bo"]
        assert shopper.put(f"/api/cart/items/{pho.id}", json={"quantity": 2}).status_code == 404

    def test_clear(self, shopper, catalog):
        add(shopper, catalog.products["pho-bo"])

        assert shopper.delete("/api/cart").status_code == 204
        assert shopper.get("/api/cart").json()["items"] == []

    def test_hides_dishes_removed_from_menu_after_adding(self, shopper, catalog, db):
        pho = catalog.products["pho-bo"]
        add(shopper, pho)
        add(shopper, catalog.products["beef-steak"])
        db.get(type(pho), pho.id).deleted_at = utcnow()
        db.commit()

        cart = shopper.get("/api/cart").json()

        assert lines(cart) == [("beef-steak", 1)]
        assert cart["total_price"] == "35.00"

    def test_carts_are_private(self, client, catalog):
        register_and_login(client, USER)
        add(client, catalog.products["pho-bo"])
        client.post("/api/auth/logout")
        register_and_login(client, {**USER, "email": "x@example.com", "phone": "0911111111"})

        assert client.get("/api/cart").json()["items"] == []


class TestGuestCart:
    def test_preview_prices_with_current_menu_and_drops_unavailable(self, client, catalog):
        products = catalog.products
        response = client.post(
            "/api/cart/preview",
            json={
                "items": [
                    {"product_id": products["beef-steak"].id, "quantity": 2},
                    {"product_id": products["old-dish"].id, "quantity": 1},
                    {"product_id": 999_999, "quantity": 1},
                    {"product_id": products["beef-steak"].id, "quantity": 1},
                ]
            },
        )

        assert response.status_code == 200
        assert lines(response.json()) == [("beef-steak", 3)]
        assert response.json()["total_price"] == "105.00"

    def test_preview_is_bounded(self, client, catalog):
        items = [{"product_id": 1, "quantity": 1}] * 101
        assert client.post("/api/cart/preview", json={"items": items}).status_code == 422

    def test_merge_after_sign_in_adds_to_existing_cart(self, shopper, catalog):
        pho, steak = catalog.products["pho-bo"], catalog.products["beef-steak"]
        add(shopper, pho, 98)

        response = shopper.post(
            "/api/cart/merge",
            json={
                "items": [
                    {"product_id": pho.id, "quantity": 5},
                    {"product_id": steak.id, "quantity": 1},
                    {"product_id": catalog.products["old-dish"].id, "quantity": 1},
                ]
            },
        )

        assert response.status_code == 200
        assert lines(response.json()) == [("pho-bo", 99), ("beef-steak", 1)]

    def test_merge_requires_sign_in(self, client, catalog):
        assert client.post("/api/cart/merge", json={"items": []}).status_code == 401
