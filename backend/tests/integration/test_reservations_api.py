from datetime import datetime, timedelta, timezone

import pytest

from app.modules.reservations import service as reservation_service
from tests.data import USER
from tests.integration.conftest import register_and_login

VIETNAM = timezone(timedelta(hours=7))
NOW = datetime(2026, 10, 29, 18, 0, tzinfo=VIETNAM)
TODAY = NOW.date()


@pytest.fixture(autouse=True)
def frozen_clock(monkeypatch):
    monkeypatch.setattr(reservation_service, "restaurant_now", lambda: NOW)


def booking(catalog, **overrides) -> dict:
    return {
        "location_id": catalog.district1.id,
        "customer_name": "Vo Van F",
        "customer_phone": "0933333333",
        "reservation_date": (TODAY + timedelta(days=1)).isoformat(),
        "reservation_time": "19:30",
        "guest_count": 4,
        "special_requests": "  Window seat, please  ",
        **overrides,
    }


def book(client, catalog, **overrides):
    return client.post("/api/reservations", json=booking(catalog, **overrides))


class TestPolicy:
    def test_describes_bookable_window(self, client):
        assert client.get("/api/reservations/policy").json() == {
            "timezone": "Asia/Ho_Chi_Minh",
            "today": "2026-10-29",
            "last_bookable_date": "2026-11-01",
            "max_guests": 10,
        }


class TestCreate:
    def test_guest_can_book_without_account(self, client, catalog):
        response = book(client, catalog)

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "PENDING"
        assert body["location"]["name"] == "District 1"
        assert body["reservation_time"] == "19:30:00"
        assert body["special_requests"] == "Window seat, please"
        assert body["can_cancel"] is True

    def test_signed_in_booking_shows_in_my_reservations(self, client, catalog):
        book(client, catalog)  # anonymous booking must not be attributed later
        register_and_login(client, USER)
        mine = book(client, catalog, reservation_date="2026-10-31").json()

        assert [r["id"] for r in client.get("/api/reservations/mine").json()] == [mine["id"]]

    @pytest.mark.parametrize(
        ("day", "time"),
        [
            (TODAY, "18:30"),  # later today
            (TODAY + timedelta(days=3), "11:00"),  # last bookable day
        ],
    )
    def test_accepts_dates_inside_window(self, client, catalog, day, time):
        response = book(client, catalog, reservation_date=day.isoformat(), reservation_time=time)
        assert response.status_code == 201

    @pytest.mark.parametrize(
        ("day", "time", "message"),
        [
            (TODAY + timedelta(days=4), "19:00", "at most 3 days in advance"),
            (TODAY - timedelta(days=1), "19:00", "cannot be in the past"),
            (TODAY, "17:59", "already passed today"),
            (TODAY, "18:00", "already passed today"),
        ],
    )
    def test_rejects_dates_outside_window(self, client, catalog, day, time, message):
        response = book(client, catalog, reservation_date=day.isoformat(), reservation_time=time)

        assert response.status_code == 400
        assert message in response.json()["detail"]

    def test_limits_party_size(self, client, catalog):
        assert book(client, catalog, guest_count=10).status_code == 201
        too_many = book(client, catalog, guest_count=11)
        assert too_many.status_code == 400
        assert "call the restaurant" in too_many.json()["detail"]

    def test_unknown_branch(self, client, catalog):
        response = book(client, catalog, location_id=999)
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "overrides",
        [
            {"guest_count": 0},
            {"customer_phone": "12345"},
            {"customer_name": "  "},
            {"reservation_date": "not-a-date"},
            {"reservation_time": "25:00"},
            {"special_requests": "x" * 1001},
        ],
    )
    def test_validates_fields(self, client, catalog, overrides):
        assert book(client, catalog, **overrides).status_code == 422


class TestMyReservations:
    def test_requires_sign_in(self, client):
        assert client.get("/api/reservations/mine").status_code == 401

    def test_latest_slot_first(self, client, catalog):
        register_and_login(client, USER)
        book(client, catalog, reservation_date="2026-10-30", reservation_time="12:00")
        book(client, catalog, reservation_date="2026-10-31", reservation_time="11:00")
        book(client, catalog, reservation_date="2026-10-30", reservation_time="20:00")

        slots = [
            (r["reservation_date"], r["reservation_time"])
            for r in client.get("/api/reservations/mine").json()
        ]
        assert slots == [
            ("2026-10-31", "11:00:00"),
            ("2026-10-30", "20:00:00"),
            ("2026-10-30", "12:00:00"),
        ]

    def test_cancel_pending_once(self, client, catalog):
        register_and_login(client, USER)
        reservation_id = book(client, catalog).json()["id"]

        cancelled = client.post(f"/api/reservations/{reservation_id}/cancel")

        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "CANCELLED"
        assert cancelled.json()["cancelled_at"] is not None
        assert client.post(f"/api/reservations/{reservation_id}/cancel").status_code == 409

    def test_cannot_cancel_someone_elses_or_anonymous_booking(self, client, catalog):
        anonymous_id = book(client, catalog).json()["id"]
        register_and_login(client, USER)
        own_id = book(client, catalog).json()["id"]
        client.post("/api/auth/logout")
        register_and_login(client, {**USER, "email": "z@example.com", "phone": "0944444444"})

        assert client.post(f"/api/reservations/{own_id}/cancel").status_code == 404
        assert client.post(f"/api/reservations/{anonymous_id}/cancel").status_code == 404
