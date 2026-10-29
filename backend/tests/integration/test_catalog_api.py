import pytest


def slugs(response) -> list[str]:
    body = response.json()
    items = body["items"] if isinstance(body, dict) else body
    return [item["slug"] for item in items]


class TestCategoriesAndLocations:
    def test_lists_categories(self, client, catalog):
        response = client.get("/api/categories")
        assert [c["slug"] for c in response.json()] == ["starters", "main_dishes"]

    def test_lists_locations_with_map_links(self, client, catalog):
        response = client.get("/api/locations")
        assert response.json()[0] == {
            "id": catalog.district1.id,
            "name": "District 1",
            "address": "1 Le Loi",
            "map_url": "https://maps/d1",
        }


class TestListProducts:
    def test_default_order_and_shape_hide_deleted_dishes(self, client, catalog):
        response = client.get("/api/products")

        assert response.status_code == 200
        body = response.json()
        assert slugs(response) == ["spring-rolls", "garlic-bread", "beef-steak", "pho-bo"]
        assert body | {"items": None} == {
            "items": None,
            "page": 1,
            "page_size": 12,
            "total": 4,
            "total_pages": 1,
        }
        steak = body["items"][2]
        assert steak["price"] == "35.00"
        assert steak["average_rating"] == "5.00"
        assert steak["image_url"] == "/media/products/main_dishes/beef-steak.webp"
        assert steak["category"] == {
            "id": catalog.mains.id,
            "name": "Main Dishes",
            "slug": "main_dishes",
        }
        assert [loc["name"] for loc in steak["locations"]] == ["District 1", "District 7"]

    def test_paginates(self, client, catalog):
        response = client.get("/api/products", params={"page": 2, "page_size": 3})

        assert slugs(response) == ["pho-bo"]
        assert response.json()["total_pages"] == 2

    def test_page_past_the_end_is_empty_not_an_error(self, client, catalog):
        response = client.get("/api/products", params={"page": 9})

        assert response.status_code == 200
        assert response.json()["items"] == []
        assert response.json()["total_pages"] == 1

    def test_filters_by_category(self, client, catalog):
        response = client.get("/api/products", params={"category": "main_dishes"})

        assert slugs(response) == ["beef-steak", "pho-bo"]
        assert response.json()["total"] == 2

    def test_unknown_category_returns_nothing(self, client, catalog):
        response = client.get("/api/products", params={"category": "desserts"})
        assert response.json()["total"] == 0

    @pytest.mark.parametrize(
        ("sort", "expected"),
        [
            ("price_asc", ["garlic-bread", "spring-rolls", "pho-bo", "beef-steak"]),
            ("price_desc", ["beef-steak", "pho-bo", "spring-rolls", "garlic-bread"]),
            # Unrated dishes go last when sorting best-first, first when worst-first.
            ("rating_desc", ["beef-steak", "spring-rolls", "pho-bo", "garlic-bread"]),
            ("rating_asc", ["garlic-bread", "pho-bo", "spring-rolls", "beef-steak"]),
        ],
    )
    def test_sorts(self, client, catalog, sort, expected):
        assert slugs(client.get("/api/products", params={"sort": sort})) == expected

    def test_sort_combines_with_category(self, client, catalog):
        response = client.get("/api/products", params={"sort": "price_asc", "category": "starters"})
        assert slugs(response) == ["garlic-bread", "spring-rolls"]

    @pytest.mark.parametrize(
        "params", [{"sort": "newest"}, {"page": 0}, {"page_size": 0}, {"page_size": 49}]
    )
    def test_rejects_invalid_params(self, client, params):
        assert client.get("/api/products", params=params).status_code == 422


class TestFeatured:
    def test_returns_highest_rated_active_dish(self, client, catalog):
        # The deleted dish is also rated 5.00 and inserted later; it must not win.
        assert client.get("/api/products/featured").json()["slug"] == "beef-steak"

    def test_returns_null_with_empty_menu(self, client):
        response = client.get("/api/products/featured")

        assert response.status_code == 200
        assert response.json() is None


class TestSearch:
    def test_is_case_insensitive_and_partial(self, client, catalog):
        assert slugs(client.get("/api/products/search", params={"q": "SPRING"})) == ["spring-rolls"]

    def test_orders_best_rated_first_with_unrated_last(self, client, catalog):
        response = client.get("/api/products/search", params={"q": "b"})
        assert slugs(response) == ["beef-steak", "pho-bo", "garlic-bread"]

    def test_limits_results(self, client, catalog):
        assert len(client.get("/api/products/search", params={"q": "e", "limit": 2}).json()) == 2

    @pytest.mark.parametrize("wildcard", ["%", "_", "\\"])
    def test_treats_like_wildcards_literally(self, client, catalog, wildcard):
        assert client.get("/api/products/search", params={"q": wildcard}).json() == []

    def test_requires_a_query(self, client):
        assert client.get("/api/products/search", params={"q": ""}).status_code == 422


class TestProductDetail:
    def test_returns_dish_by_slug(self, client, catalog):
        response = client.get("/api/products/pho-bo")

        assert response.status_code == 200
        assert response.json()["name"] == "Pho Bo"

    @pytest.mark.parametrize("slug", ["no-such-dish", "old-dish"])
    def test_missing_or_deleted_dish_is_404(self, client, catalog, slug):
        response = client.get(f"/api/products/{slug}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Dish not found."
