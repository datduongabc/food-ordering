import csv
import io
from datetime import datetime

from sqlalchemy import select

from app.modules.orders.models import OrderStatus, PaymentMethod, PaymentStatus
from app.modules.reservations.models import Reservation
from app.modules.users.models import User
from tests.data import USER
from tests.integration.conftest import ADMIN
from tests.integration.test_admin_api import VIETNAM, customer_id, make_order


def entries(client, **filters) -> list[dict]:
    response = client.get("/api/admin/audit-log", params=filters)
    assert response.status_code == 200, response.text
    return response.json()["items"]


def new_dish(client, catalog, **overrides):
    return client.post(
        "/api/admin/products",
        json={
            "name": {"vi": "Phở Bò Đặc Biệt", "en": "Special Beef Pho"},
            "description": {"vi": "Phở bò đặc biệt", "en": "Special beef noodle soup"},
            "price": 145_000,
            "category_id": catalog.mains.id,
            "location_ids": [catalog.district1.id],
            **overrides,
        },
    )


def read_csv(response) -> list[list[str]]:
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text.startswith("﻿")
    return list(csv.reader(io.StringIO(response.text.removeprefix("﻿"))))


class TestAuditLog:
    def test_records_who_created_a_dish_and_its_fields(self, admin_client, catalog):
        dish = new_dish(admin_client, catalog).json()

        [entry] = entries(admin_client)
        assert entry["action"] == "product.create"
        assert entry["actor_name"] == ADMIN["name"]
        assert (entry["target_type"], entry["target_id"]) == ("product", dish["id"])
        assert entry["target_label"] == "Phở Bò Đặc Biệt"
        assert entry["changes"]["price"] == [None, 145_000]

    def test_records_only_the_fields_an_edit_changed(self, admin_client, catalog):
        dish_id = new_dish(admin_client, catalog).json()["id"]

        admin_client.patch(
            f"/api/admin/products/{dish_id}",
            json={"price": 150_000, "location_ids": [catalog.district7.id]},
        )
        # Saving without changes leaves nothing to record.
        admin_client.patch(f"/api/admin/products/{dish_id}", json={"price": 150_000})

        [update, _] = entries(admin_client, target_type="product", target_id=dish_id)
        assert update["action"] == "product.update"
        assert update["changes"] == {
            "price": [145_000, 150_000],
            "location_ids": [[catalog.district1.id], [catalog.district7.id]],
        }

    def test_a_refused_change_leaves_no_entry(self, admin_client, catalog):
        new_dish(admin_client, catalog, slug="pho-bo")  # taken by the catalog
        assert entries(admin_client) == []

    def test_records_hiding_restoring_and_photos(self, admin_client, catalog):
        dish_id = catalog.products["pho-bo"].id
        admin_client.post(f"/api/admin/products/{dish_id}/hide")
        admin_client.post(f"/api/admin/products/{dish_id}/hide")  # already hidden
        admin_client.post(f"/api/admin/products/{dish_id}/restore")
        admin_client.put(
            f"/api/admin/products/{dish_id}/image",
            files={"image": ("pho.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, "image/png")},
        )

        actions = [entry["action"] for entry in entries(admin_client, action="product")]
        assert actions == ["product.image", "product.restore", "product.hide"]

    def test_records_order_and_booking_status_changes(self, admin_client, customer, db, catalog):
        order = make_order(db, customer_id(db), [(catalog.products["pho-bo"], 1)])
        admin_client.post(
            f"/api/admin/orders/{order.id}/status", json={"status": "CONFIRMED", "note": "Gọi lại"}
        )
        booking = Reservation(
            user_id=customer_id(db),
            location_id=catalog.district1.id,
            customer_name="Nguyen Van A",
            customer_phone="0901234567",
            reservation_date=datetime(2026, 11, 1).date(),
            reservation_time=datetime(2026, 11, 1, 18).time(),
            guest_count=2,
        )
        db.add(booking)
        db.commit()
        admin_client.post(
            f"/api/admin/reservations/{booking.id}/status", json={"status": "CONFIRMED"}
        )

        [booked, confirmed] = entries(admin_client)
        assert confirmed["action"] == "order.status"
        assert confirmed["target_label"] == f"#{order.id}"
        assert confirmed["changes"] == {
            "status": ["PENDING", "CONFIRMED"],
            "note": [None, "Gọi lại"],
        }
        assert booked["action"] == "reservation.status"
        assert booked["changes"] == {"status": ["PENDING", "CONFIRMED"]}

    def test_never_records_a_password(self, admin_client, db):
        created = admin_client.post(
            "/api/admin/users",
            json={
                "name": "Nhan Vien",
                "email": "staff@dateno.vn",
                "phone": "0977777777",
                "password": "staff-password",
                "role": "CUSTOMER",
                "email_verified": False,
            },
        ).json()
        admin_client.patch(
            f"/api/admin/users/{created['id']}",
            json={"password": "another-password", "role": "ADMIN"},
        )
        admin_client.post(f"/api/admin/users/{created['id']}/deactivate")
        admin_client.post(f"/api/admin/users/{created['id']}/restore")

        log = entries(admin_client, action="user")
        assert [entry["action"] for entry in log] == [
            "user.restore",
            "user.deactivate",
            "user.update",
            "user.create",
        ]
        assert log[2]["changes"] == {"role": ["CUSTOMER", "ADMIN"], "password": ["••••••"] * 2}
        assert log[3]["changes"]["password"] == [None, "••••••"]
        assert "staff-password" not in str(log) and "another-password" not in str(log)

    def test_entries_survive_the_admin_being_renamed(self, admin_client, catalog, db):
        new_dish(admin_client, catalog)
        admin = db.scalar(select(User).where(User.email == ADMIN["email"]))
        admin.name = "Renamed"
        db.commit()

        assert entries(admin_client)[0]["actor_name"] == ADMIN["name"]

    def test_pages_newest_first(self, admin_client, catalog):
        for dish in catalog.products.values():
            admin_client.post(f"/api/admin/products/{dish.id}/hide")

        page = admin_client.get("/api/admin/audit-log", params={"page_size": 1}).json()
        # One dish in the catalog is already hidden, so hiding it again records nothing.
        assert page["total"] == page["total_pages"] == len(catalog.products) - 1


class TestExports:
    def test_orders_csv_lists_the_range_in_local_time_and_is_logged(
        self, admin_client, customer, db, catalog
    ):
        uid = customer_id(db)
        pho = catalog.products["pho-bo"]
        make_order(db, uid, [(pho, 2)], created_at=datetime(2026, 10, 1, 0, 30, tzinfo=VIETNAM))
        make_order(
            db,
            uid,
            [(pho, 1)],
            status=OrderStatus.COMPLETED,
            method=PaymentMethod.MOMO,
            payment_status=PaymentStatus.PAID,
            created_at=datetime(2026, 10, 2, 23, 59, tzinfo=VIETNAM),
        )
        # Outside the range by a minute, in restaurant time.
        make_order(db, uid, [(pho, 1)], created_at=datetime(2026, 10, 3, 0, 0, tzinfo=VIETNAM))

        rows = read_csv(
            admin_client.get("/api/admin/exports/orders.csv?from=2026-10-01&to=2026-10-02")
        )

        assert rows[0][:3] == ["Mã đơn", "Thời gian đặt", "Khách hàng"]
        assert [row[1] for row in rows[1:]] == ["2026-10-01 00:30", "2026-10-02 23:59"]
        assert rows[1][2:4] == [USER["name"], USER["email"]]
        assert rows[1][8:10] == ["2", str(pho.price * 2)]
        assert rows[2][10:13] == ["Hoàn thành", "Ví MoMo", "Đã thanh toán"]
        [entry] = entries(admin_client, action="export")
        assert entry["action"] == "export.orders"
        assert entry["changes"]["rows"] == [None, 2]

    def test_orders_csv_filters_by_status_and_speaks_english(
        self, admin_client, customer, db, catalog
    ):
        uid = customer_id(db)
        pho = catalog.products["pho-bo"]
        when = datetime(2026, 10, 5, 12, tzinfo=VIETNAM)
        make_order(db, uid, [(pho, 1)], created_at=when)
        make_order(db, uid, [(pho, 1)], status=OrderStatus.CANCELLED, created_at=when)

        response = admin_client.get(
            "/api/admin/exports/orders.csv",
            params={"from": "2026-10-05", "to": "2026-10-05", "status": "CANCELLED", "lang": "en"},
        )
        rows = read_csv(response)

        assert rows[0][0] == "Order"
        assert [row[10] for row in rows[1:]] == ["Cancelled"]
        assert (
            "dateno-orders-2026-10-05_2026-10-05-cancelled.csv"
            in (response.headers["content-disposition"])
        )

    def test_cells_cannot_become_spreadsheet_formulas(self, admin_client, customer, db, catalog):
        order = make_order(
            db,
            customer_id(db),
            [(catalog.products["pho-bo"], 1)],
            created_at=datetime(2026, 10, 5, 12, tzinfo=VIETNAM),
        )
        order.delivery_address = '=HYPERLINK("http://evil.example","Click")'
        order.delivery_name = "+84 Nguyen"
        db.commit()

        [_, row] = read_csv(
            admin_client.get("/api/admin/exports/orders.csv?from=2026-10-05&to=2026-10-05")
        )
        assert row[6] == '\'=HYPERLINK("http://evil.example","Click")'
        assert row[4] == "'+84 Nguyen"

    def test_revenue_csv_has_every_day_and_a_total(self, admin_client, customer, db, catalog):
        uid = customer_id(db)
        pho = catalog.products["pho-bo"]
        make_order(
            db,
            uid,
            [(pho, 2)],
            status=OrderStatus.COMPLETED,
            created_at=datetime(2026, 10, 1, 9, tzinfo=VIETNAM),
        )
        make_order(db, uid, [(pho, 1)], created_at=datetime(2026, 10, 3, 9, tzinfo=VIETNAM))

        rows = read_csv(
            admin_client.get("/api/admin/exports/revenue.csv?from=2026-10-01&to=2026-10-03")
        )

        assert rows == [
            ["Ngày", "Đơn đã đặt", "Đơn hoàn thành", "Doanh thu (VND)"],
            ["2026-10-01", "1", "1", str(pho.price * 2)],
            ["2026-10-02", "0", "0", "0"],
            ["2026-10-03", "1", "0", "0"],
            ["Tổng", "2", "1", str(pho.price * 2)],
        ]
        assert entries(admin_client)[0]["action"] == "export.revenue"

    def test_rejects_backwards_or_overlong_ranges(self, admin_client):
        for query in ("from=2026-10-05&to=2026-10-01", "from=2025-01-01&to=2026-10-01"):
            response = admin_client.get(f"/api/admin/exports/revenue.csv?{query}")
            assert response.status_code == 400
            assert response.json()["code"] == "invalid_date_range"
        assert entries(admin_client) == []
