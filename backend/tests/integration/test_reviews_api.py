from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.core.db import utcnow
from app.modules.feedback.models import Review
from app.modules.feedback.service import refresh_rating
from app.modules.orders.models import OrderStatus
from app.modules.users.models import User
from tests.data import USER
from tests.integration.conftest import register_and_login
from tests.integration.test_admin_api import make_order
from tests.integration.test_admin_audit_api import entries
from tests.photos import opened, photo

OTHER_USER = {**USER, "name": "Le Thi C", "email": "c@example.com", "phone": "0907654321"}


def post_review(client, slug="pho-bo", rating=5, comment="Delicious"):
    return client.post(f"/api/products/{slug}/reviews", json={"rating": rating, "comment": comment})


def user_id(db, email) -> int:
    return db.scalar(select(User.id).where(User.email == email))


def delivered(db, catalog, email=USER["email"], *slugs, status=OrderStatus.COMPLETED):
    """An order of the dishes that reached the customer (or stopped at `status`)."""
    lines = [(catalog.products[slug], 1) for slug in slugs or ("pho-bo",)]
    return make_order(db, user_id(db, email), lines, status)


def reviewer(client, db, catalog, user=USER, *slugs):
    """Signs `user` in with a delivered order of the dishes, ready to review them."""
    register_and_login(client, user)
    delivered(db, catalog, user["email"], *slugs)
    return client


def reviews_of(client, slug="pho-bo", **params):
    return client.get(f"/api/products/{slug}/reviews", params=params).json()


class TestAddReview:
    def test_requires_sign_in(self, client, catalog):
        assert post_review(client).status_code == 401

    def test_creates_a_verified_review_and_recomputes_average_and_count(self, client, catalog, db):
        reviewer(client, db, catalog)
        response = post_review(client, rating=5, comment="  Rich broth  ")

        assert response.status_code == 201
        body = response.json()
        assert (body["rating"], body["comment"]) == (5, "Rich broth")
        assert (body["user_name"], body["verified_purchase"]) == (USER["name"], True)
        # The fixture's 3.50 came from no stored reviews, so the first real one replaces it.
        dish = client.get("/api/products/pho-bo").json()
        assert (dish["average_rating"], dish["review_count"]) == ("5.00", 1)

        client.post("/api/auth/logout")
        reviewer(client, db, catalog, OTHER_USER)
        assert post_review(client, rating=4).status_code == 201
        dish = client.get("/api/products/pho-bo").json()
        assert (dish["average_rating"], dish["review_count"]) == ("4.50", 2)

    @pytest.mark.parametrize(
        "status", [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.CANCELLED]
    )
    def test_needs_a_delivered_order_of_that_dish(self, client, catalog, db, status):
        register_and_login(client, USER)
        delivered(db, catalog, USER["email"], "pho-bo", status=status)
        delivered(db, catalog, USER["email"], "beef-steak")

        response = post_review(client, slug="pho-bo")

        assert response.status_code == 403
        assert response.json()["code"] == "review_needs_purchase"
        assert reviews_of(client)["total"] == 0

    def test_someone_elses_order_does_not_count(self, client, catalog, db):
        register_and_login(client, OTHER_USER)
        delivered(db, catalog, OTHER_USER["email"])
        client.post("/api/auth/logout")
        register_and_login(client, USER)

        assert post_review(client).status_code == 403

    def test_one_review_per_user_per_dish(self, client, catalog, db):
        reviewer(client, db, catalog, USER, "pho-bo", "beef-steak")
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


class TestEligibility:
    def eligibility(self, client, slug="pho-bo"):
        return client.get(f"/api/products/{slug}/reviews/eligibility")

    def test_explains_why_the_form_is_closed(self, client, catalog, db):
        assert self.eligibility(client).status_code == 401
        register_and_login(client, USER)
        assert self.eligibility(client).json() == {
            "can_review": False,
            "reason": "not_purchased",
        }

        delivered(db, catalog)
        assert self.eligibility(client).json() == {"can_review": True, "reason": None}

        post_review(client)
        assert self.eligibility(client).json() == {
            "can_review": False,
            "reason": "already_reviewed",
        }

    def test_unknown_dish(self, client, catalog):
        register_and_login(client, USER)
        assert self.eligibility(client, "nope").status_code == 404


def seed_reviews(db, catalog, ratings: list[int], slug="pho-bo") -> list[Review]:
    """Reviews by fresh customers, oldest first, with the dish's stored rating refreshed."""
    now = utcnow()
    product = catalog.products[slug]
    reviews = []
    first = db.scalar(select(func.count(User.id)))
    for i, rating in enumerate(ratings):
        n = first + i
        user = User(
            name=f"Khach {i}",
            email=f"k{n}@example.com",
            phone=f"09{n:08d}",
            password_hash="x",
        )
        review = Review(
            user=user,
            product_id=product.id,
            rating=rating,
            comment=f"review {i}",
            verified_purchase=True,
            created_at=now - timedelta(minutes=len(ratings) - i),
        )
        db.add(review)
        reviews.append(review)
    db.flush()
    refresh_rating(db, product.id)
    db.commit()
    return reviews


class TestListReviews:
    def test_newest_first_without_private_reviewer_data(self, client, catalog, db):
        seed_reviews(db, catalog, [4, 5])

        body = reviews_of(client)

        assert [r["comment"] for r in body["items"]] == ["review 1", "review 0"]
        assert set(body["items"][0]) == {
            "id",
            "rating",
            "comment",
            "created_at",
            "user_name",
            "verified_purchase",
            "reply",
            "replied_at",
            "photos",
        }

    def test_summary_counts_every_star(self, client, catalog, db):
        seed_reviews(db, catalog, [5, 5, 4, 1])

        summary = reviews_of(client, page_size=1)["summary"]

        assert (summary["average"], summary["count"]) == ("3.75", 4)
        assert summary["distribution"] == [
            {"stars": 5, "count": 2},
            {"stars": 4, "count": 1},
            {"stars": 3, "count": 0},
            {"stars": 2, "count": 0},
            {"stars": 1, "count": 1},
        ]

    def test_pages_filters_and_sorts(self, client, catalog, db):
        seed_reviews(db, catalog, [5, 2, 5, 3, 5])

        first = reviews_of(client, page_size=2)
        assert (first["total"], first["total_pages"]) == (5, 3)
        assert [r["comment"] for r in reviews_of(client, page_size=2, page=3)["items"]] == [
            "review 0"
        ]

        fives = reviews_of(client, rating=5)
        assert [r["comment"] for r in fives["items"]] == ["review 4", "review 2", "review 0"]
        assert fives["summary"]["count"] == 5  # the summary ignores the filter

        assert [r["rating"] for r in reviews_of(client, sort="lowest")["items"]] == [2, 3, 5, 5, 5]
        highest = reviews_of(client, sort="highest")["items"]
        assert [r["comment"] for r in highest[:3]] == ["review 4", "review 2", "review 0"]

    @pytest.mark.parametrize(
        "params", [{"rating": 0}, {"rating": 6}, {"sort": "oldest"}, {"page_size": 51}]
    )
    def test_rejects_invalid_params(self, client, catalog, params):
        assert client.get("/api/products/pho-bo/reviews", params=params).status_code == 422

    def test_unknown_dish_is_404(self, client, catalog):
        assert client.get("/api/products/nope/reviews").status_code == 404


class TestModeration:
    def review_id(self, db, catalog):
        return seed_reviews(db, catalog, [5, 1])[1].id

    def test_hiding_takes_a_review_off_the_page_and_out_of_the_rating(
        self, admin_client, catalog, db
    ):
        rude = self.review_id(db, catalog)

        hidden = admin_client.post(f"/api/admin/reviews/{rude}/hide").json()
        admin_client.post(f"/api/admin/reviews/{rude}/hide")  # already hidden: no second entry

        assert hidden["hidden_at"] is not None
        assert [r["rating"] for r in reviews_of(admin_client)["items"]] == [5]
        dish = admin_client.get("/api/products/pho-bo").json()
        assert (dish["average_rating"], dish["review_count"]) == ("5.00", 1)
        assert reviews_of(admin_client)["summary"]["distribution"][-1] == {"stars": 1, "count": 0}
        top = admin_client.get("/api/reviews/top").json()
        assert [r["rating"] for r in top] == [5]

        admin_client.post(f"/api/admin/reviews/{rude}/restore")
        dish = admin_client.get("/api/products/pho-bo").json()
        assert (dish["average_rating"], dish["review_count"]) == ("3.00", 2)

        log = entries(admin_client, action="review")
        assert [e["action"] for e in log] == ["review.restore", "review.hide"]
        assert log[0]["target_label"] == "Khach 1: Phở bò (1★)"

    def test_staff_reply_shows_under_the_review_and_can_be_removed(self, admin_client, catalog, db):
        review = self.review_id(db, catalog)

        reply = admin_client.put(
            f"/api/admin/reviews/{review}/reply", json={"reply": "  Xin lỗi quý khách!  "}
        ).json()
        assert reply["reply"] == "Xin lỗi quý khách!"
        shown = reviews_of(admin_client)["items"][0]
        assert (shown["reply"], shown["replied_at"] is not None) == ("Xin lỗi quý khách!", True)

        admin_client.put(f"/api/admin/reviews/{review}/reply", json={"reply": " "})
        assert reviews_of(admin_client)["items"][0]["reply"] is None

        log = entries(admin_client, action="review.reply")
        assert [e["changes"]["reply"] for e in log] == [
            ["Xin lỗi quý khách!", None],
            [None, "Xin lỗi quý khách!"],
        ]

    def test_lists_and_filters_every_review(self, admin_client, catalog, db):
        five, one = seed_reviews(db, catalog, [5, 1])
        seed_reviews(db, catalog, [3], slug="beef-steak")
        admin_client.post(f"/api/admin/reviews/{one.id}/hide")

        def listed(**params):
            body = admin_client.get("/api/admin/reviews", params=params).json()
            return [(r["product_slug"], r["rating"]) for r in body["items"]]

        assert listed() == [("beef-steak", 3), ("pho-bo", 1), ("pho-bo", 5)]
        assert listed(visibility="hidden") == [("pho-bo", 1)]
        assert listed(visibility="visible") == [("beef-steak", 3), ("pho-bo", 5)]
        assert listed(rating=5) == [("pho-bo", 5)]
        assert listed(product="pho-bo") == [("pho-bo", 1), ("pho-bo", 5)]

    def test_unknown_review(self, admin_client):
        assert admin_client.post("/api/admin/reviews/999/hide").status_code == 404

    def test_customers_cannot_moderate(self, customer, catalog, db):
        review = self.review_id(db, catalog)
        assert customer.post(f"/api/admin/reviews/{review}/hide").status_code == 403
        assert customer.get("/api/admin/reviews").status_code == 403


class TestPhotos:
    def upload(self, client, review_id, content=None, name="dish.jpg"):
        return client.post(
            f"/api/reviews/{review_id}/photos",
            files={
                "photo": (
                    name,
                    photo("JPEG", (2400, 1800), gps=True) if content is None else content,
                )
            },
        )

    @pytest.fixture
    def review(self, client, catalog, db):
        reviewer(client, db, catalog)
        return post_review(client).json()

    def test_stores_up_to_three_resized_photos_with_thumbnails(self, client, review, media_dir):
        for _ in range(3):
            assert self.upload(client, review["id"]).status_code == 201

        fourth = self.upload(client, review["id"])
        assert fourth.status_code == 409
        assert fourth.json()["code"] == "review_photos_full"

        photos = reviews_of(client)["items"][0]["photos"]
        assert len(photos) == 3
        first = photos[0]
        assert first["url"].startswith(f"/media/reviews/{review['id']}-")
        assert first["thumbnail_url"].startswith(f"/media/reviews/thumbs/{review['id']}-")
        stored = opened((media_dir / first["url"].removeprefix("/media/")).read_bytes())
        assert (stored.format, max(stored.size)) == ("WEBP", 1200)
        assert "GPSInfo" not in str(stored.getexif())
        thumb = opened((media_dir / first["thumbnail_url"].removeprefix("/media/")).read_bytes())
        assert max(thumb.size) == 640

    def test_only_the_author_shortly_after_posting(self, client, review, db):
        client.post("/api/auth/logout")
        register_and_login(client, OTHER_USER)
        assert self.upload(client, review["id"]).status_code == 404

        client.post("/api/auth/logout")
        client.post("/api/auth/login", json={"email": USER["email"], "password": USER["password"]})
        db.get(Review, review["id"]).created_at = utcnow() - timedelta(hours=2)
        db.commit()
        late = self.upload(client, review["id"])
        assert late.status_code == 403
        assert late.json()["code"] == "review_photos_closed"

    def test_rejects_files_that_are_not_photos(self, client, review):
        for content in (b"GIF89a not allowed", b"\x89PNG\r\n\x1a\n broken"):
            response = self.upload(client, review["id"], content)
            assert response.status_code == 400
            assert response.json()["code"] == "image_type_not_allowed"
        empty = self.upload(client, review["id"], b"")
        assert empty.json()["code"] == "empty_upload"

    def test_not_on_a_hidden_review(self, client, review, db):
        db.get(Review, review["id"]).hidden_at = utcnow()
        db.commit()
        assert self.upload(client, review["id"]).status_code == 404


class TestTopReviews:
    def test_best_rating_first_then_newest_and_skips_deleted_dishes(self, client, catalog, db):
        register_and_login(client, USER)
        uid = user_id(db, USER["email"])
        now = utcnow()
        products = catalog.products
        db.add_all(
            [
                Review(
                    user_id=uid,
                    product_id=products["pho-bo"].id,
                    rating=4,
                    comment="good",
                    created_at=now,
                ),
                Review(
                    user_id=uid,
                    product_id=products["beef-steak"].id,
                    rating=5,
                    comment="older five",
                    created_at=now - timedelta(days=2),
                ),
                Review(
                    user_id=uid,
                    product_id=products["spring-rolls"].id,
                    rating=5,
                    comment="newer five",
                    created_at=now - timedelta(days=1),
                ),
                Review(
                    user_id=uid,
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
        assert body[0]["product_name"]["en"] == "Shrimp Spring Rolls"
        assert body[0]["product_slug"] == "spring-rolls"
        assert body[0]["user_name"] == USER["name"]


class TestRanking:
    def test_many_good_reviews_outrank_a_single_perfect_one(self, client, catalog, db):
        # Beef steak keeps the fixture's one 5.00; pho gets twenty reviews averaging 4.80.
        seed_reviews(db, catalog, [5] * 16 + [4] * 4)

        best = client.get("/api/products", params={"sort": "rating_desc"}).json()["items"]

        assert [d["slug"] for d in best[:2]] == ["pho-bo", "beef-steak"]
        assert (best[0]["average_rating"], best[0]["review_count"]) == ("4.80", 20)
        assert client.get("/api/products/featured").json()["slug"] == "pho-bo"
