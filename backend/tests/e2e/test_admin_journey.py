"""Staff running the shop: add a dish, take an order through to completion, read the numbers."""

import uuid

from app.core.config import BACKEND_DIR


def sign_in(browser, email: str, password: str) -> None:
    browser.post("/api/auth/login", json={"email": email, "password": password}).raise_for_status()


def test_admin_adds_dish_and_fulfils_an_order(server, new_browser):
    suffix = uuid.uuid4().hex[:8]
    admin_email = f"admin-{suffix}@dateno.vn"
    server.create_admin(admin_email, "Quan Ly", f"03{int(suffix, 16) % 10**8:08d}", "admin-pass-1")
    admin = new_browser()
    sign_in(admin, admin_email, "admin-pass-1")
    before = admin.get("/api/admin/dashboard").json()

    # A new dish with a Vietnamese name and a real photo.
    branches = admin.get("/api/locations").json()
    mains = next(c for c in admin.get("/api/categories").json() if c["slug"] == "main_dishes")
    dish = admin.post(
        "/api/admin/products",
        json={
            "name": {"vi": f"Bún chả Hà Nội {suffix}", "en": f"Hanoi Grilled Pork {suffix}"},
            "description": {
                "vi": "Chả nướng ăn kèm bún và rau thơm",
                "en": "Grilled pork with rice vermicelli and herbs",
            },
            "price": 290_000,
            "category_id": mains["id"],
            "location_ids": [branches[0]["id"]],
        },
    ).json()
    assert dish["slug"] == f"hanoi-grilled-pork-{suffix}"
    photo = (BACKEND_DIR / "media" / "products" / "placeholder.webp").read_bytes()
    dish = admin.put(
        f"/api/admin/products/{dish['id']}/image", files={"image": ("bun-cha.webp", photo)}
    ).json()
    assert admin.get(dish["image_url"]).content == photo
    assert (server.media_dir / dish["image_url"].removeprefix("/media/")).exists()

    # A customer orders it for delivery from the only branch that makes it.
    customer = new_browser()
    email = f"h-{suffix}@example.com"
    customer.post(
        "/api/auth/register",
        json={
            "name": "Bui Van H",
            "email": email,
            "password": "customer-pass",
            "phone": f"04{int(suffix, 16) % 10**8:08d}",
        },
    ).raise_for_status()
    sign_in(customer, email, "customer-pass")
    customer.post("/api/cart/items", json={"product_id": dish["id"], "quantity": 2})
    form = {
        "payment_method": "COD",
        "delivery_name": "Bui Van H",
        "delivery_phone": "0966666666",
        "delivery_address": "99 Pasteur, District 3",
    }
    wrong_branch = customer.post("/api/orders", json={**form, "location_id": branches[1]["id"]})
    assert wrong_branch.status_code == 400
    order = customer.post("/api/orders", json={**form, "location_id": branches[0]["id"]}).json()

    # Staff confirm and complete it; cash is collected on delivery.
    for status in ("CONFIRMED", "COMPLETED"):
        admin.post(
            f"/api/admin/orders/{order['id']}/status", json={"status": status}
        ).raise_for_status()
    seen = customer.get(f"/api/orders/{order['id']}").json()
    assert (seen["status"], seen["payment_status"]) == ("COMPLETED", "PAID")
    assert [e["to_status"] for e in seen["events"]] == ["PENDING", "CONFIRMED", "COMPLETED"]

    after = admin.get("/api/admin/dashboard").json()
    assert after["completed_orders"] == before["completed_orders"] + 1
    assert after["completed_revenue"] == before["completed_revenue"] + 580_000
    top = admin.get("/api/admin/stats/top-dishes", params={"limit": 20}).json()
    assert any(d["slug"] == dish["slug"] and d["quantity"] == 2 for d in top["by_quantity"])
    today = admin.get("/api/admin/stats/revenue", params={"days": 1}).json()
    assert float(today["total_revenue"]) >= 23.00
