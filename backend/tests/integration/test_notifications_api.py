import pytest

from app.core.config import get_settings
from tests.data import USER
from tests.integration.test_momo_gateway_api import (
    ACCESS_KEY,
    PARTNER,
    SECRET_KEY,
    fake_momo,  # noqa: F401  (fixture)
    momo_result,
    query_string,
    start,
)
from tests.integration.test_orders_api import checkout, fill_cart
from tests.integration.test_reservations_api import book, frozen_clock  # noqa: F401


@pytest.fixture(autouse=True)
def public_url(monkeypatch):
    monkeypatch.setattr(get_settings(), "public_url", "https://dateno.example/")


@pytest.fixture
def inbox(outbox):
    """The outbox without the sign-up verification emails sent while setting up."""
    outbox.sent.clear()
    return outbox


def subjects(outbox) -> list[str]:
    return [email.subject for email in outbox.sent]


def place(client, catalog, method="COD") -> int:
    fill_cart(client, catalog, pho_bo=2)
    response = checkout(client, method)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def set_status(admin_client, kind, target_id, status, **extra):
    response = admin_client.post(
        f"/api/admin/{kind}/{target_id}/status", json={"status": status, **extra}
    )
    assert response.status_code == 200, response.text


class TestOrderEmails:
    def test_placing_an_order_sends_its_summary_in_both_languages(self, shopper, catalog, inbox):
        order_id = place(shopper, catalog)

        [email] = inbox.sent
        assert email.to == USER["email"]
        assert email.subject == f"DaTeNO: Đã nhận đơn hàng #{order_id} / Order #{order_id} received"
        pho = catalog.products["pho-bo"]
        assert f"2 x {pho.name['vi']}" in email.text and f"2 x {pho.name['en']}" in email.text
        assert "Tiền mặt khi nhận hàng" in email.text and "Cash on delivery" in email.text
        assert "Nhà hàng sẽ gọi xác nhận" in email.text
        assert f"https://dateno.example/account?order={order_id}" in email.text
        assert email.text.index("English version") > email.text.index("Chào")

    def test_a_momo_order_waits_for_payment(self, shopper, catalog, inbox):
        place(shopper, catalog, "MOMO")
        [email] = inbox.sent
        assert "hoàn tất thanh toán MoMo" in email.text
        assert "as soon as your MoMo payment goes through" in email.text

    def test_staff_confirm_and_deliver_with_their_note(
        self, admin_client, customer, catalog, inbox
    ):
        order_id = place(customer, catalog)
        set_status(admin_client, "orders", order_id, "CONFIRMED", note="Giao trước 12h")
        set_status(admin_client, "orders", order_id, "COMPLETED")

        placed, confirmed, delivered = inbox.sent
        assert confirmed.subject.endswith(f"Order #{order_id} confirmed")
        assert "Lời nhắn từ nhà hàng: Giao trước 12h" in confirmed.text
        assert "Message from the restaurant: Giao trước 12h" in confirmed.text
        assert delivered.subject.endswith(f"Order #{order_id} delivered")
        # One review link per dish, even ordered twice, in both languages.
        assert delivered.text.count("https://dateno.example/menu/pho-bo#reviews") == 2
        assert "  Phở bò: https://dateno.example/menu/pho-bo#reviews" in delivered.text
        assert "  Pho Bo: https://dateno.example/menu/pho-bo#reviews" in delivered.text
        assert "\n\nHow was it? A review helps" in delivered.text

    def test_staff_cancelling_apologises(self, admin_client, customer, catalog, inbox):
        order_id = place(customer, catalog)
        set_status(admin_client, "orders", order_id, "CANCELLED", note="Hết món")

        cancelled = inbox.sent[-1]
        assert "nhà hàng đã phải hủy đơn hàng" in cancelled.text
        assert "Sorry, we had to cancel" in cancelled.text
        assert "Hết món" in cancelled.text

    def test_customer_cancelling_gets_a_receipt(self, shopper, catalog, inbox):
        order_id = place(shopper, catalog)
        shopper.post(f"/api/orders/{order_id}/cancel")

        cancelled = inbox.sent[-1]
        assert cancelled.subject.endswith(f"Order #{order_id} cancelled")
        assert "Quý khách đã hủy đơn hàng" in cancelled.text
        assert "You cancelled order" in cancelled.text
        assert "hoàn lại" not in cancelled.text

    def test_cancelling_a_paid_order_mentions_the_refund(
        self, admin_client, customer, catalog, inbox
    ):
        order_id = place(customer, catalog, "MOMO")
        attempt = customer.post(f"/api/orders/{order_id}/payments/momo").json()
        customer.post(
            "/api/payments/momo/sandbox/complete",
            json={"momo_order_id": attempt["momo_order_id"], "result": "approved"},
        )
        set_status(admin_client, "orders", order_id, "CANCELLED")

        placed, paid, cancelled = inbox.sent
        assert paid.subject.endswith(f"Payment received for order #{order_id}")
        assert "qua ví MoMo" in paid.text
        assert "will be refunded" in cancelled.text

    def test_a_declined_payment_sends_nothing(self, shopper, catalog, inbox):
        order_id = place(shopper, catalog, "MOMO")
        attempt = shopper.post(f"/api/orders/{order_id}/payments/momo").json()
        shopper.post(
            "/api/payments/momo/sandbox/complete",
            json={"momo_order_id": attempt["momo_order_id"], "result": "declined"},
        )
        assert len(inbox.sent) == 1

    def test_a_failing_mail_server_does_not_fail_the_order(self, shopper, catalog, inbox):
        def broken(_email):
            raise ConnectionError("SMTP down")

        inbox.send = broken
        fill_cart(shopper, catalog, pho_bo=1)
        assert checkout(shopper).status_code == 201


class TestMomoGatewayEmails:
    @pytest.fixture(autouse=True)
    def live_keys(self, monkeypatch):
        settings = get_settings()
        monkeypatch.setattr(settings, "momo_partner_code", PARTNER)
        monkeypatch.setattr(settings, "momo_access_key", ACCESS_KEY)
        monkeypatch.setattr(settings, "momo_secret_key", SECRET_KEY)

    def pay(self, client, catalog) -> tuple[int, dict]:
        order_id = place(client, catalog, "MOMO")
        total = client.get(f"/api/orders/{order_id}").json()["total_price"]
        return order_id, momo_result(start(client, order_id)["momo_order_id"], amount=total)

    def test_return_and_ipn_together_send_one_email(self, shopper, catalog, fake_momo, inbox):  # noqa: F811
        order_id, result = self.pay(shopper, catalog)

        assert shopper.post("/api/payments/momo/return", json=query_string(result)).is_success
        assert shopper.post("/api/payments/momo/ipn", json=result).status_code == 204

        assert subjects(inbox)[1:] == [
            f"DaTeNO: Đã nhận thanh toán đơn #{order_id} / Payment received for order #{order_id}"
        ]

    def test_ipn_alone_sends_the_payment_email(self, shopper, catalog, fake_momo, inbox):  # noqa: F811
        order_id, result = self.pay(shopper, catalog)

        shopper.post("/api/payments/momo/ipn", json=result)
        assert len(inbox.sent) == 2


class TestBookingEmails:
    def test_a_signed_in_booking_is_acknowledged(self, shopper, catalog, inbox):
        booking_id = book(shopper, catalog).json()["id"]

        [email] = inbox.sent
        assert email.to == USER["email"]
        assert email.subject.endswith(f"Booking request #{booking_id} received")
        assert "Số khách: 4" in email.text and "Guests: 4" in email.text
        assert "Yêu cầu: Window seat, please" in email.text
        assert "Friday 30 October 2026 at 19:30" in email.text
        assert "Thứ Sáu, 30/10/2026 lúc 19:30" in email.text
        assert "https://dateno.example/account?tab=bookings" in email.text

    def test_a_guest_booking_has_nobody_to_email(self, client, catalog, inbox):
        assert book(client, catalog).status_code == 201
        assert inbox.sent == []

    def test_staff_confirming_and_cancelling(self, admin_client, customer, catalog, inbox):
        first = book(customer, catalog).json()["id"]
        second = book(customer, catalog, reservation_time="20:00").json()["id"]
        set_status(admin_client, "reservations", first, "CONFIRMED")
        set_status(admin_client, "reservations", second, "CANCELLED")
        set_status(admin_client, "reservations", first, "COMPLETED")

        _, _, confirmed, cancelled = inbox.sent
        assert confirmed.to == USER["email"]
        assert confirmed.subject.endswith(f"Booking #{first} confirmed")
        assert "See you soon" in confirmed.text
        assert cancelled.subject.endswith(f"Booking #{second} cancelled")
        assert "nhà hàng không thể giữ bàn" in cancelled.text

    def test_customer_cancelling(self, shopper, catalog, inbox):
        booking_id = book(shopper, catalog).json()["id"]
        shopper.post(f"/api/reservations/{booking_id}/cancel")

        cancelled = inbox.sent[-1]
        assert "Quý khách đã hủy đặt bàn" in cancelled.text
        assert "You cancelled this booking" in cancelled.text
