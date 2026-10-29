from datetime import timedelta

import pytest

from app.core.db import utcnow
from app.modules.feedback.models import Review
from tests.data import USER
from tests.integration.conftest import register_and_login

OTHER_USER = {**USER, "name": "Le Thi C", "email": "c@example.com", "phone": "0907654321"}


def post_review(client, slug="pho-bo", rating=5, comment="Delicious"):
    return client.post(f"/api/products/{slug}/reviews", json={"rating": rating, "comment": comment})


class TestAddReview:
    def test_requires_sign_in(self, client, catalog):
        assert post_review(client).status_code == 401

    def test_creates_review_and_recomputes_average(self, client, catalog):
        register_and_login(client, USER)
        response = post_review(client, rating=5, comment="  Rich broth  ")

        assert response.status_code == 201
        body = response.json()
        assert body["rating"] == 5
        assert body["comment"] == "Rich broth"
        assert body["user_name"] == USER["name"]
        # Seed rating 3.50 came from no stored reviews, so the first real review replaces it.
        assert client.get("/api/products/pho-bo").json()["average_rating"] == "5.00"

        client.post("/api/auth/logout")
        register_and_login(client, OTHER_USER)
        assert post_review(client, rating=4).status_code == 201
        assert client.get("/api/products/pho-bo").json()["average_rating"] == "4.50"

    def test_one_review_per_user_per_dish(self, client, catalog):
        register_and_login(client, USER)
        assert post_review(client).status_code == 201

        again = post_review(client, rating=1)

        assert again.status_code == 409
        assert again.json()["code"] == "already_reviewed"
        assert post_review(client, slug="beef-steak").status_code == 201

    @pytest.mark.parametrize(
        "payload",
        [
            {"rating": 0, "comment": "ok"},
            {"rating": 6, "comment": "ok"},
            {"rating": 5, "comment": "   "},
            {"rating": 5, "comment": "x" * 2001},
            {"rating": 5},
        ],
    )
    def test_validates_payload(self, client, catalog, payload):
        register_and_login(client, USER)
        assert client.post("/api/products/pho-bo/reviews", json=payload).status_code == 422

    def test_cannot_review_deleted_dish(self, client, catalog):
        register_and_login(client, USER)
        assert post_review(client, slug="old-dish").status_code == 404


class TestListReviews:
    def test_newest_first_without_private_reviewer_data(self, client, catalog, db):
        register_and_login(client, USER)
        post_review(client, comment="first")
        client.post("/api/auth/logout")
        register_and_login(client, OTHER_USER)
        post_review(client, comment="second")

        response = client.get("/api/products/pho-bo/reviews")

        assert [r["comment"] for r in response.json()] == ["second", "first"]
        assert set(response.json()[0]) == {"id", "rating", "comment", "created_at", "user_name"}

    def test_unknown_dish_is_404(self, client, catalog):
        assert client.get("/api/products/nope/reviews").status_code == 404


class TestTopReviews:
    def test_best_rating_first_then_newest_and_skips_deleted_dishes(self, client, catalog, db):
        register_and_login(client, USER)
        user_id = client.get("/api/auth/me").json()["id"]
        now = utcnow()
        products = catalog.products
        db.add_all(
            [
                Review(
                    user_id=user_id,
                    product_id=products["pho-bo"].id,
                    rating=4,
                    comment="good",
                    created_at=now,
                ),
                Review(
                    user_id=user_id,
                    product_id=products["beef-steak"].id,
                    rating=5,
                    comment="older five",
                    created_at=now - timedelta(days=2),
                ),
                Review(
                    user_id=user_id,
                    product_id=products["spring-rolls"].id,
                    rating=5,
                    comment="newer five",
                    created_at=now - timedelta(days=1),
                ),
                Review(
                    user_id=user_id,
                    product_id=products["old-dish"].id,
                    rating=5,
                    comment="retired",
                    created_at=now,
                ),
            ]
        )
        db.commit()

        response = client.get("/api/reviews/top", params={"limit": 3})

        body = response.json()
        assert [r["comment"] for r in body] == ["newer five", "older five", "good"]
        assert body[0]["product_name"] == "Shrimp Spring Rolls"
        assert body[0]["product_slug"] == "spring-rolls"
        assert body[0]["user_name"] == USER["name"]
