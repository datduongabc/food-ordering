from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import select

from app.modules.admin import stats as admin_stats
from app.modules.orders.models import (
    Order,
    OrderEvent,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.modules.reservations.models import Reservation, ReservationStatus
from app.modules.users.models import User
from tests.data import USER
from tests.integration.conftest import ADMIN, register_and_login

VIETNAM = timezone(timedelta(hours=7))
NOW = datetime(2026, 10, 29, 12, 0, tzinfo=VIETNAM)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 64


def customer_id(db) -> int:
    return db.scalar(select(User.id).where(User.email == USER["email"]))


def make_order(
    db,
    user_id: int,
    lines: list[tuple],
    status=OrderStatus.PENDING,
    created_at: datetime = NOW,
    method=PaymentMethod.COD,
    payment_status=PaymentStatus.UNPAID,
) -> Order:
    order = Order(
        user_id=user_id,
        status=status,
        payment_method=method,
        payment_status=payment_status,
        created_at=created_at,
        delivery_name="Khach Hang",
        delivery_phone="0901234567",
        delivery_address="1 Le Loi",
        items=[OrderItem(product=p, price_at_purchase=p.price, quantity=q) for p, q in lines],
        events=[OrderEvent(from_status=None, to_status=OrderStatus.PENDING)],
    )
    order.total_price = sum(i.price_at_purchase * i.quantity for i in order.items)
    db.add(order)
    db.commit()
    return order


@pytest.fixture
def customer(second_client, catalog):
    """A signed-in customer in a separate browser from the admin."""
    register_and_login(second_client, USER)
    return second_client


class TestAccess:
    ENDPOINTS = [
        ("get", "/api/admin/dashboard"),
        ("get", "/api/admin/stats/revenue"),
        ("get", "/api/admin/products"),
        ("post", "/api/admin/products/1/hide"),
        ("get", "/api/admin/orders"),
        ("post", "/api/admin/orders/1/status"),
        ("get", "/api/admin/reservations"),
        ("get", "/api/admin/users"),
        ("post", "/api/admin/users/1/deactivate"),
    ]

    @pytest.mark.parametrize(("method", "path"), ENDPOINTS)
    def test_anonymous_gets_401(self, client, method, path):
        assert getattr(client, method)(path).status_code == 401

    @pytest.mark.parametrize(("method", "path"), ENDPOINTS)
    def test_customer_gets_403(self, client, method, path):
        register_and_login(client, USER)
        assert getattr(client, method)(path).status_code == 403

    def test_demoted_admin_loses_access_immediately(self, admin_client, db):
        admin = db.scalar(select(User).where(User.email == ADMIN["email"]))
        admin.role = "CUSTOMER"
        db.commit()
        assert admin_client.get("/api/admin/dashboard").status_code == 403


class TestOrders:
    def test_lists_newest_first_with_customer_and_filter(self, admin_client, customer, catalog, db):
        uid = customer_id(db)
        first = make_order(db, uid, [(catalog.products["pho-bo"], 1)], created_at=NOW)
        second = make_order(
            db,
            uid,
            [(catalog.products["beef-steak"], 1)],
            status=OrderStatus.CONFIRMED,
            created_at=NOW + timedelta(minutes=5),
        )

        page = admin_client.get("/api/admin/orders").json()
        assert [o["id"] for o in page["items"]] == [second.id, first.id]
        assert page["total"] == 2
        assert page["items"][0]["customer"] == {
            "id": uid,
            "name": USER["name"],
            "email": USER["email"],
            "phone": USER["phone"],
        }

        pending = admin_client.get("/api/admin/orders", params={"status": "PENDING"}).json()
        assert [o["id"] for o in pending["items"]] == [first.id]

    def test_paginates(self, admin_client, customer, catalog, db):
        for _ in range(3):
            make_order(db, customer_id(db), [(catalog.products["pho-bo"], 1)])
        page = admin_client.get("/api/admin/orders", params={"page": 2, "page_size": 2}).json()
        assert (len(page["items"]), page["total"], page["total_pages"]) == (1, 3, 2)

    def test_cod_order_lifecycle_records_who_did_what(self, admin_client, customer, catalog, db):
        order = make_order(db, customer_id(db), [(catalog.products["pho-bo"], 2)])

        def move(status, note=""):
            return admin_client.post(
                f"/api/admin/orders/{order.id}/status", json={"status": status, "note": note}
            )

        assert move("CONFIRMED", "Kitchen started").status_code == 200
        done = move("COMPLETED").json()

        assert (done["status"], done["payment_status"]) == ("COMPLETED", "PAID")  # cash collected
        assert [(e["to_status"], e["actor_name"], e["note"]) for e in done["events"]] == [
            ("PENDING", None, ""),
            ("CONFIRMED", ADMIN["name"], "Kitchen started"),
            ("COMPLETED", ADMIN["name"], ""),
        ]
        # The customer sees the same timeline, without staff names.
        seen = customer.get(f"/api/orders/{order.id}").json()
        assert [e["to_status"] for e in seen["events"]] == ["PENDING", "CONFIRMED", "COMPLETED"]

    @pytest.mark.parametrize(
        ("start", "target"),
        [
            (OrderStatus.PENDING, "COMPLETED"),
            (OrderStatus.PENDING, "PENDING"),
            (OrderStatus.COMPLETED, "CANCELLED"),
            (OrderStatus.CANCELLED, "CONFIRMED"),
        ],
    )
    def test_rejects_invalid_steps(self, admin_client, customer, catalog, db, start, target):
        order = make_order(db, customer_id(db), [(catalog.products["pho-bo"], 1)], status=start)

        response = admin_client.post(
            f"/api/admin/orders/{order.id}/status", json={"status": target}
        )

        assert response.status_code == 409
        assert response.json()["code"] == "invalid_status_transition"
        assert response.json()["params"] == {"from": start, "to": target}

    def test_cancelling_a_paid_order_marks_it_for_refund(self, admin_client, customer, catalog, db):
        order = make_order(
            db,
            customer_id(db),
            [(catalog.products["beef-steak"], 1)],
            status=OrderStatus.CONFIRMED,
            method=PaymentMethod.MOMO,
            payment_status=PaymentStatus.PAID,
        )

        cancelled = admin_client.post(
            f"/api/admin/orders/{order.id}/status", json={"status": "CANCELLED"}
        ).json()

        assert cancelled["payment_status"] == "REFUNDED"
        assert (cancelled["events"][-1]["actor"], cancelled["events"][-1]["note"]) == ("staff", "")

    def test_missing_order(self, admin_client):
        assert admin_client.get("/api/admin/orders/999").status_code == 404


class TestReservations:
    @pytest.fixture
    def bookings(self, db, catalog):
        def book(day, at, status=ReservationStatus.PENDING):
            reservation = Reservation(
                location_id=catalog.district1.id,
                customer_name="Khach",
                customer_phone="0900000000",
                reservation_date=day,
                reservation_time=at,
                guest_count=2,
                status=status,
            )
            db.add(reservation)
            db.commit()
            return reservation

        return [
            book(date(2026, 10, 31), time(19, 0)),
            book(date(2026, 10, 30), time(20, 0)),
            book(date(2026, 10, 30), time(11, 30), ReservationStatus.CONFIRMED),
        ]

    def test_lists_soonest_first_and_filters(self, admin_client, bookings):
        ids = [r["id"] for r in admin_client.get("/api/admin/reservations").json()["items"]]
        assert ids == [bookings[2].id, bookings[1].id, bookings[0].id]

        by_day = admin_client.get("/api/admin/reservations", params={"date": "2026-10-30"})
        assert by_day.json()["total"] == 2
        confirmed = admin_client.get("/api/admin/reservations", params={"status": "CONFIRMED"})
        assert [r["id"] for r in confirmed.json()["items"]] == [bookings[2].id]

    def test_status_steps(self, admin_client, bookings):
        pending = bookings[0]

        def move(status):
            return admin_client.post(
                f"/api/admin/reservations/{pending.id}/status", json={"status": status}
            )

        assert move("COMPLETED").status_code == 409  # must be confirmed first
        assert move("CONFIRMED").json()["status"] == "CONFIRMED"
        cancelled = move("CANCELLED").json()
        assert cancelled["status"] == "CANCELLED"
        assert cancelled["cancelled_at"] is not None
        assert move("CONFIRMED").status_code == 409


class TestProducts:
    def create(self, client, catalog, **overrides):
        return client.post(
            "/api/admin/products",
            json={
                "name": {"vi": "Phở Bò Đặc Biệt", "en": "Special Beef Pho"},
                "description": {"vi": "Phở bò đặc biệt", "en": "Special beef noodle soup"},
                "price": 145_000,
                "category_id": catalog.mains.id,
                "location_ids": [catalog.district1.id, catalog.district7.id],
                **overrides,
            },
        )

    def test_lists_hidden_dishes_too(self, admin_client, catalog):
        slugs = {p["slug"]: p["deleted_at"] for p in admin_client.get("/api/admin/products").json()}
        assert len(slugs) == 5
        assert slugs["old-dish"] is not None

    def test_create_stores_both_languages_and_slugs_the_english_name(self, admin_client, catalog):
        response = self.create(admin_client, catalog)

        assert response.status_code == 201
        dish = response.json()
        assert dish["name"] == {"vi": "Phở Bò Đặc Biệt", "en": "Special Beef Pho"}
        assert dish["description"]["vi"] == "Phở bò đặc biệt"
        assert dish["slug"] == "special-beef-pho"
        assert dish["price"] == 145_000
        assert dish["image_url"] == "/media/products/placeholder.webp"
        assert [loc["id"] for loc in dish["locations"]] == [
            catalog.district1.id,
            catalog.district7.id,
        ]
        assert admin_client.get("/api/products/special-beef-pho").status_code == 200

    def test_duplicate_slug_conflicts(self, admin_client, catalog):
        response = self.create(admin_client, catalog, slug="pho-bo")
        assert response.status_code == 409

    @pytest.mark.parametrize(
        ("overrides", "code"),
        [
            ({"category_id": 999}, 400),
            ({"location_ids": [999]}, 400),
            ({"location_ids": []}, 422),
            ({"price": "0"}, 422),
            ({"price": "1.234"}, 422),
            ({"slug": "Bad Slug"}, 422),
            ({"name": {"vi": "Phở", "en": "  "}}, 422),
            ({"name": "Phở"}, 422),
        ],
    )
    def test_validates(self, admin_client, catalog, overrides, code):
        assert self.create(admin_client, catalog, **overrides).status_code == code

    def test_update_changes_only_given_fields(self, admin_client, catalog):
        pho = catalog.products["pho-bo"]
        response = admin_client.patch(
            f"/api/admin/products/{pho.id}",
            json={"price": 130_000, "location_ids": [catalog.district1.id]},
        )

        dish = response.json()
        assert (dish["name"]["en"], dish["price"]) == ("Pho Bo", 130_000)
        assert [loc["name"]["en"] for loc in dish["locations"]] == ["District 1"]

    def test_update_replaces_both_translations(self, admin_client, catalog):
        pho = catalog.products["pho-bo"]
        response = admin_client.patch(
            f"/api/admin/products/{pho.id}",
            json={"name": {"vi": "Phở bò tái", "en": "Rare Beef Pho"}},
        )

        assert response.json()["name"] == {"vi": "Phở bò tái", "en": "Rare Beef Pho"}
        assert response.json()["slug"] == "pho-bo"

    def test_hide_and_restore(self, admin_client, catalog):
        pho = catalog.products["pho-bo"]

        assert admin_client.post(f"/api/admin/products/{pho.id}/hide").json()["deleted_at"]
        assert admin_client.get("/api/products/pho-bo").status_code == 404

        assert (
            admin_client.post(f"/api/admin/products/{pho.id}/restore").json()["deleted_at"] is None
        )
        assert admin_client.get("/api/products/pho-bo").status_code == 200

    @pytest.mark.parametrize(
        ("content", "extension"), [(PNG, "png"), (JPEG, "jpg"), (WEBP, "webp")]
    )
    def test_image_upload_detects_real_format(
        self, admin_client, catalog, media_dir, content, extension
    ):
        pho = catalog.products["pho-bo"]

        response = admin_client.put(
            f"/api/admin/products/{pho.id}/image",
            files={"image": ("photo.gif", content, "image/gif")},  # name and type are ignored
        )

        assert response.status_code == 200
        url = response.json()["image_url"]
        assert url.startswith("/media/products/uploads/pho-bo-") and url.endswith(f".{extension}")
        assert (media_dir / url.removeprefix("/media/")).read_bytes() == content
        assert admin_client.get(url).content == content

    def test_new_upload_replaces_previous_file(self, admin_client, catalog, media_dir):
        pho = catalog.products["pho-bo"]

        def upload():
            return admin_client.put(
                f"/api/admin/products/{pho.id}/image", files={"image": ("a.png", PNG)}
            ).json()["image_url"]

        first, second = upload(), upload()

        assert first != second
        assert not (media_dir / first.removeprefix("/media/")).exists()
        assert (media_dir / second.removeprefix("/media/")).exists()

    @pytest.mark.parametrize(
        ("content", "code"),
        [
            (b"GIF89a" + b"\x00" * 64, "image_type_not_allowed"),
            (b"<?php echo 1; ?>", "image_type_not_allowed"),
            (PNG + b"\x00" * (5 * 1024 * 1024), "image_too_large"),
            (b"", "empty_upload"),
        ],
    )
    def test_rejects_bad_uploads(self, admin_client, catalog, content, code):
        pho = catalog.products["pho-bo"]
        response = admin_client.put(
            f"/api/admin/products/{pho.id}/image", files={"image": ("x.png", content)}
        )
        assert response.status_code == 400
        assert response.json()["code"] == code


class TestUsers:
    def admin_id(self, db) -> int:
        return db.scalar(select(User.id).where(User.email == ADMIN["email"]))

    def test_lists_and_searches(self, admin_client, customer):
        everyone = admin_client.get("/api/admin/users").json()
        assert [u["email"] for u in everyone["items"]] == [ADMIN["email"], USER["email"]]

        found = admin_client.get("/api/admin/users", params={"q": "nguyen"}).json()
        assert [u["email"] for u in found["items"]] == [USER["email"]]
        assert admin_client.get("/api/admin/users", params={"q": "%"}).json()["total"] == 0

    def test_create_user(self, admin_client):
        response = admin_client.post(
            "/api/admin/users",
            json={
                "name": "Nhan Vien",
                "email": "Staff@DaTeNO.vn",
                "phone": "0977777777",
                "password": "staff-password",
                "role": "ADMIN",
                "email_verified": True,
            },
        )

        assert response.status_code == 201
        assert response.json()["email"] == "staff@dateno.vn"
        assert response.json()["is_email_verified"] is True

    def test_duplicate_email_conflicts(self, admin_client, customer):
        response = admin_client.post(
            "/api/admin/users",
            json={**USER, "phone": "0988888888", "password": "whatever-123"},
        )
        assert response.status_code == 409

    def test_update_role_and_verification(self, admin_client, customer, db):
        uid = customer_id(db)
        response = admin_client.patch(
            f"/api/admin/users/{uid}", json={"role": "ADMIN", "email_verified": True}
        )

        assert (response.json()["role"], response.json()["is_email_verified"]) == ("ADMIN", True)
        assert customer.get("/api/admin/dashboard").status_code == 200

    def test_cannot_demote_or_deactivate_self(self, admin_client, db):
        me = self.admin_id(db)
        assert (
            admin_client.patch(f"/api/admin/users/{me}", json={"role": "CUSTOMER"}).status_code
            == 400
        )
        assert admin_client.post(f"/api/admin/users/{me}/deactivate").status_code == 400

    def test_deactivate_signs_customer_out_and_restore_allows_login(
        self, admin_client, customer, db
    ):
        uid = customer_id(db)

        response = admin_client.post(f"/api/admin/users/{uid}/deactivate")

        assert response.json()["deleted_at"] is not None
        assert customer.get("/api/auth/me").status_code == 401
        hidden = admin_client.get("/api/admin/users").json()["items"]
        assert USER["email"] not in [u["email"] for u in hidden]
        shown = admin_client.get("/api/admin/users", params={"include_deactivated": True})
        assert USER["email"] in [u["email"] for u in shown.json()["items"]]

        admin_client.post(f"/api/admin/users/{uid}/restore")
        login = customer.post(
            "/api/auth/login", json={"email": USER["email"], "password": USER["password"]}
        )
        assert login.status_code == 200

    def test_admin_set_password_signs_customer_out(self, admin_client, customer, db):
        admin_client.patch(
            f"/api/admin/users/{customer_id(db)}", json={"password": "reset-by-staff"}
        )

        assert customer.get("/api/auth/me").status_code == 401
        login = customer.post(
            "/api/auth/login", json={"email": USER["email"], "password": "reset-by-staff"}
        )
        assert login.status_code == 200


class TestDashboardAndStats:
    @pytest.fixture(autouse=True)
    def frozen_clock(self, monkeypatch):
        monkeypatch.setattr(admin_stats, "restaurant_now", lambda: NOW)

    @pytest.fixture
    def history(self, admin_client, customer, catalog, db):
        uid = customer_id(db)
        p = catalog.products
        # Today: one completed COD order and one pending MoMo order that failed to pay.
        make_order(
            db,
            uid,
            [(p["pho-bo"], 2)],
            OrderStatus.COMPLETED,
            method=PaymentMethod.COD,
            payment_status=PaymentStatus.PAID,
        )
        make_order(
            db,
            uid,
            [(p["beef-steak"], 1)],
            OrderStatus.PENDING,
            method=PaymentMethod.MOMO,
            payment_status=PaymentStatus.FAILED,
        )
        # 00:30 on Oct 28 in Vietnam is still Oct 27 in UTC; it must count for the 28th.
        make_order(
            db,
            uid,
            [(p["beef-steak"], 2)],
            OrderStatus.COMPLETED,
            created_at=datetime(2026, 10, 28, 0, 30, tzinfo=VIETNAM),
            method=PaymentMethod.MOMO,
            payment_status=PaymentStatus.PAID,
        )
        # Cancelled orders and orders outside the window never count as sales.
        make_order(db, uid, [(p["spring-rolls"], 9)], OrderStatus.CANCELLED)
        make_order(
            db,
            uid,
            [(p["spring-rolls"], 5)],
            OrderStatus.COMPLETED,
            created_at=NOW - timedelta(days=40),
        )

    def test_summary(self, admin_client, history):
        assert admin_client.get("/api/admin/dashboard").json() == {
            "completed_revenue": 1_415_000,  # 240,000 + 700,000 + 475,000
            "completed_orders": 3,
            "average_order_value": 471_667,
            "total_orders": 5,
            "pending_orders": 1,
            "active_products": 4,
            "customers": 1,
            "total_reservations": 0,
            "pending_reservations": 0,
        }

    def test_revenue_trend_groups_by_vietnam_day(self, admin_client, history):
        trend = admin_client.get("/api/admin/stats/revenue", params={"days": 3}).json()

        assert trend["days"] == [
            {"date": "2026-10-27", "orders": 0, "revenue": 0},
            {"date": "2026-10-28", "orders": 1, "revenue": 700_000},
            {"date": "2026-10-29", "orders": 2, "revenue": 240_000},
        ]
        assert (trend["total_orders"], trend["total_revenue"]) == (3, 940_000)

    def test_top_dishes(self, admin_client, history):
        top = admin_client.get(
            "/api/admin/stats/top-dishes", params={"days": 30, "limit": 2}
        ).json()

        assert [(d["slug"], d["quantity"], d["revenue"]) for d in top["by_quantity"]] == [
            ("beef-steak", 3, 1_050_000),
            ("pho-bo", 2, 240_000),
        ]
        assert [d["slug"] for d in top["by_revenue"]] == ["beef-steak", "pho-bo"]
        # Spring rolls only sold in a cancelled order and 40 days ago: zero in this window.
        assert [(d["slug"], d["quantity"]) for d in top["least_sold"]] == [
            ("spring-rolls", 0),
            ("garlic-bread", 0),
        ]

    def test_payments(self, admin_client, history):
        assert admin_client.get("/api/admin/stats/payments", params={"days": 30}).json() == {
            "cod_orders": 2,
            "momo_orders": 2,
            "momo": {"paid": 1, "failed": 1, "success_rate": 0.5},
        }

    def test_ratings(self, admin_client, customer, catalog):
        customer.post("/api/products/pho-bo/reviews", json={"rating": 2, "comment": "Too salty"})
        customer.post("/api/products/beef-steak/reviews", json={"rating": 5, "comment": "Perfect"})

        ratings = admin_client.get("/api/admin/stats/ratings").json()

        assert [
            (d["slug"], d["average_rating"], d["review_count"]) for d in ratings["lowest_rated"]
        ] == [
            ("pho-bo", "2.00", 1),
            ("beef-steak", "5.00", 1),
        ]
        assert [r["comment"] for r in ratings["latest_reviews"]] == ["Perfect", "Too salty"]

    def test_empty_shop(self, admin_client):
        assert admin_client.get("/api/admin/stats/payments").json()["momo"]["success_rate"] is None
        assert admin_client.get("/api/admin/dashboard").json()["average_order_value"] == 0
