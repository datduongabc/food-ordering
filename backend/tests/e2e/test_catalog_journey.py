"""Browsing the real seeded menu (from the Alembic seed migration) over HTTP.

The server is shared by the whole e2e session and other journeys add dishes, so these
checks look for the seeded dishes rather than assuming the menu holds nothing else.
"""

import math
import uuid
from urllib.parse import parse_qs, urlsplit


def all_slugs(browser, **params) -> list[str]:
    body = browser.get("/api/products", params={"page_size": 48, **params}).json()
    return [item["slug"] for item in body["items"]]


def test_browse_menu_seeded_by_migrations(new_browser):
    browser = new_browser()

    first_page = browser.get("/api/products").json()
    total = first_page["total"]
    assert total >= 30
    assert first_page["total_pages"] == math.ceil(total / 12)
    assert len(first_page["items"]) == 12
    # Default order is by id, so the seeded dishes come first, starters before mains.
    assert first_page["items"][0]["slug"] == "caesar-salad"

    last_page = browser.get("/api/products", params={"page": first_page["total_pages"]}).json()
    assert len(last_page["items"]) == total - 12 * (first_page["total_pages"] - 1)

    mains = all_slugs(browser, category="main_dishes")
    assert {"peking-roast-duck", "beef-steak-red-wine", "thai-seafood-hotpot"} <= set(mains)
    assert "caesar-salad" not in mains

    assert {"wagyu-beef-pho", "hanoi-bun-cha", "tamarind-crab"} <= set(mains)
    assert len(all_slugs(browser, category="desserts")) == 10
    assert "egg-coffee" in all_slugs(browser, category="drinks")

    cheapest = browser.get("/api/products", params={"sort": "price_asc"}).json()["items"][0]
    assert cheapest["name"] == {"vi": "Nước mía tắc", "en": "Sugarcane Juice with Kumquat"}
    assert [loc["name"]["vi"] for loc in cheapest["locations"]] == [
        "DaTeNO - Quận 1",
        "DaTeNO - Quận 7",
        "DaTeNO - Thủ Đức",
    ]

    first_branch = browser.get("/api/locations").json()[0]
    assert first_branch["name"] == {"vi": "DaTeNO - Quận 1", "en": "DaTeNO - District 1"}


def test_branch_map_links_search_for_the_branch_address(new_browser):
    # The PHP seed shipped short links that 404'd; every branch must point at its own address.
    for location in new_browser().get("/api/locations").json():
        url = urlsplit(location["map_url"])
        assert (url.scheme, url.netloc, url.path) == ("https", "www.google.com", "/maps/search/")
        assert parse_qs(url.query) == {"api": ["1"], "query": [location["address"]["vi"]]}


def test_dish_images_are_served(new_browser):
    browser = new_browser()
    dish = browser.get("/api/products/caesar-salad").json()

    image = browser.get(dish["image_url"])

    assert image.status_code == 200
    assert image.headers["content-type"] == "image/webp"
    assert len(image.content) > 1000


def test_search_then_only_buyers_may_review(new_browser):
    browser = new_browser()
    results = browser.get("/api/products/search", params={"q": "spring roll"}).json()
    assert {r["slug"] for r in results} == {"seafood-spring-rolls-mayo", "shrimp-pork-spring-rolls"}

    suffix = uuid.uuid4().hex[:8]
    customer = {
        "name": "Pham Van D",
        "email": f"d-{suffix}@example.com",
        "password": "review-password",
        "phone": f"08{int(suffix, 16) % 10**8:08d}",
    }
    assert browser.post("/api/auth/register", json=customer).status_code == 201
    browser.post(
        "/api/auth/login", json={"email": customer["email"], "password": customer["password"]}
    ).raise_for_status()

    slug = "shrimp-pork-spring-rolls"
    assert browser.get(f"/api/products/{slug}/reviews/eligibility").json() == {
        "can_review": False,
        "reason": "not_purchased",
    }
    review = browser.post(
        f"/api/products/{slug}/reviews",
        json={"rating": 5, "comment": "Fresh herbs, perfect peanut sauce."},
    )
    assert review.status_code == 403
    assert review.json()["code"] == "review_needs_purchase"
    summary = browser.get(f"/api/products/{slug}/reviews").json()["summary"]
    assert len(summary["distribution"]) == 5
