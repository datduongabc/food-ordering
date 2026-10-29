"""Booking a table against a real server, using the live restaurant clock."""

import uuid
from datetime import date, timedelta


def test_book_view_and_cancel_a_table(new_browser):
    browser = new_browser()
    policy = browser.get("/api/reservations/policy").json()
    tomorrow = date.fromisoformat(policy["today"]) + timedelta(days=1)
    assert date.fromisoformat(policy["last_bookable_date"]) == tomorrow + timedelta(days=2)
    branch = browser.get("/api/locations").json()[2]

    form = {
        "location_id": branch["id"],
        "customer_name": "Dang Thi G",
        "customer_phone": "0955555555",
        "reservation_date": tomorrow.isoformat(),
        "reservation_time": "19:00",
        "guest_count": policy["max_guests"],
    }
    assert browser.post("/api/reservations", json=form).status_code == 201  # as a guest

    day_after_window = date.fromisoformat(policy["last_bookable_date"]) + timedelta(days=1)
    too_far = {**form, "reservation_date": day_after_window.isoformat()}
    assert browser.post("/api/reservations", json=too_far).status_code == 400

    suffix = uuid.uuid4().hex[:8]
    customer = {
        "name": "Dang Thi G",
        "email": f"g-{suffix}@example.com",
        "password": "booking-password",
        "phone": f"06{int(suffix, 16) % 10**8:08d}",
    }
    browser.post("/api/auth/register", json=customer).raise_for_status()
    browser.post(
        "/api/auth/login", json={"email": customer["email"], "password": customer["password"]}
    ).raise_for_status()

    booked = browser.post("/api/reservations", json=form).json()
    mine = browser.get("/api/reservations/mine").json()
    assert [(r["id"], r["location"]["name"]["en"]) for r in mine] == [
        (booked["id"], "DaTeNO - Thu Duc")
    ]

    cancelled = browser.post(f"/api/reservations/{booked['id']}/cancel").json()
    assert cancelled["status"] == "CANCELLED"
