"""Browsing the real seeded menu (from the Alembic seed migration) over HTTP."""

import uuid


def test_browse_menu_seeded_by_migrations(new_browser):
    browser = new_browser()

    first_page = browser.get("/api/products").json()
    assert first_page["total"] == 30
    assert first_page["total_pages"] == 3
    assert len(first_page["items"]) == 12

    last_page = browser.get("/api/products", params={"page": 3}).json()
    assert len(last_page["items"]) == 6

    mains = browser.get("/api/products", params={"category": "main_dishes", "page_size": 48})
    assert mains.json()["total"] == 18

    cheapest = browser.get("/api/products", params={"sort": "price_asc"}).json()["items"][0]
    assert cheapest["name"] == "Garlic Butter Bread"
    assert [loc["name"] for loc in cheapest["locations"]] == [
        "DaTeNO - District 1",
        "DaTeNO - District 7",
        "DaTeNO - Thu Duc",
    ]

    assert [loc["name"] for loc in browser.get("/api/locations").json()][0] == "DaTeNO - District 1"


def test_dish_images_are_served(new_browser):
    browser = new_browser()
    dish = browser.get("/api/products/caesar-salad").json()

    image = browser.get(dish["image_url"])

    assert image.status_code == 200
    assert image.headers["content-type"] == "image/webp"
    assert len(image.content) > 1000


def test_search_then_review_changes_ratings_and_featured_dish(new_browser):
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

    review = browser.post(
        "/api/products/shrimp-pork-spring-rolls/reviews",
        json={"rating": 5, "comment": "Fresh herbs, perfect peanut sauce."},
    )
    assert review.status_code == 201

    dish = browser.get("/api/products/shrimp-pork-spring-rolls").json()
    assert dish["average_rating"] == "5.00"
    reviews = browser.get("/api/products/shrimp-pork-spring-rolls/reviews").json()
    assert reviews[0]["user_name"] == "Pham Van D"
    top = browser.get("/api/reviews/top").json()
    assert any(r["product_slug"] == "shrimp-pork-spring-rolls" for r in top)
    assert browser.get("/api/products/featured").json()["average_rating"] == "5.00"
