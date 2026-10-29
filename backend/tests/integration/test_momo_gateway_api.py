import io
import json
import urllib.error

import pytest

from app.core.config import get_settings
from app.modules.orders import momo
from tests.integration.test_orders_api import checkout, fill_cart

PARTNER = "MOMOTEST"
ACCESS_KEY = "access-key"
SECRET_KEY = "secret-key"


@pytest.fixture(autouse=True)
def live_keys(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "momo_partner_code", PARTNER)
    monkeypatch.setattr(settings, "momo_access_key", ACCESS_KEY)
    monkeypatch.setattr(settings, "momo_secret_key", SECRET_KEY)
    monkeypatch.setattr(settings, "public_url", "https://dateno.example/")


class FakeMomo:
    """Stands in for MoMo's create endpoint and records what it was sent."""

    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.answer: dict | Exception = {}

    def __call__(self, request, timeout):
        body = json.loads(request.data)
        self.requests.append({"url": request.full_url, "body": body, "timeout": timeout})
        if isinstance(self.answer, Exception):
            raise self.answer
        return io.BytesIO(
            json.dumps(
                self.answer
                or {"resultCode": 0, "payUrl": f"https://momo.example/{body['orderId']}"}
            ).encode()
        )


@pytest.fixture
def fake_momo(monkeypatch) -> FakeMomo:
    fake = FakeMomo()
    monkeypatch.setattr(momo.urllib.request, "urlopen", fake)
    return fake


@pytest.fixture
def order_id(shopper, catalog) -> int:
    fill_cart(shopper, catalog, pho_bo=2, beef_steak=1)  # 590,000 VND
    return checkout(shopper, "MOMO").json()["id"]


def momo_result(momo_order_id: str, result_code: int = 0, amount: int = 590_000, **overrides):
    """What MoMo sends to the IPN and appends to the redirect URL, signed with our key."""
    fields = {
        "amount": amount,
        "extraData": "",
        "message": "Successful." if result_code == 0 else "Declined.",
        "orderId": momo_order_id,
        "orderInfo": "Thanh toan don hang",
        "orderType": "momo_wallet",
        "partnerCode": PARTNER,
        "payType": "qr",
        "requestId": momo_order_id,
        "responseTime": 1798000000000,
        "resultCode": result_code,
        "transId": 4100000001,
    }
    signed = momo.sign(SECRET_KEY, {"accessKey": ACCESS_KEY, **fields})
    return {**fields, "signature": signed, **overrides}


def start(client, order_id) -> dict:
    response = client.post(f"/api/orders/{order_id}/payments/momo")
    assert response.status_code == 200, response.text
    return response.json()


def query_string(params: dict) -> dict:
    # The browser's copy arrives as a query string, so every value is text.
    return {key: str(value) for key, value in params.items()}


class TestStartingAPayment:
    def test_registers_a_signed_payment_and_returns_its_pay_url(self, shopper, order_id, fake_momo):
        attempt = start(shopper, order_id)

        assert attempt["mode"] == "gateway"
        assert attempt["pay_url"] == f"https://momo.example/{attempt['momo_order_id']}"
        [sent] = fake_momo.requests
        body = sent["body"]
        assert sent["url"] == "https://test-payment.momo.vn/v2/gateway/api/create"
        assert body["amount"] == 590_000
        assert body["orderId"] == body["requestId"] == attempt["momo_order_id"]
        assert body["redirectUrl"] == "https://dateno.example/payment/momo/return"
        assert body["ipnUrl"] == "https://dateno.example/api/payments/momo/ipn"
        assert "accessKey" not in body
        signed = {k: v for k, v in body.items() if k not in ("lang", "signature")}
        assert body["signature"] == momo.sign(SECRET_KEY, {"accessKey": ACCESS_KEY, **signed})

    @pytest.mark.parametrize(
        "answer",
        [
            urllib.error.URLError("connection refused"),
            urllib.error.HTTPError("u", 500, "", {}, io.BytesIO(b'{"resultCode": 99}')),
            TimeoutError(),
            {"resultCode": 1001, "message": "Insufficient balance"},
        ],
    )
    def test_momo_failures_leave_the_order_untouched(self, shopper, order_id, fake_momo, answer):
        fake_momo.answer = answer

        response = shopper.post(f"/api/orders/{order_id}/payments/momo")

        assert response.status_code == 503
        assert response.json()["code"] == "momo_unreachable"
        assert shopper.get(f"/api/orders/{order_id}").json()["payment_status"] == "UNPAID"

    def test_sandbox_is_closed_once_live_keys_are_set(self, shopper, order_id, fake_momo):
        attempt = start(shopper, order_id)
        response = shopper.post(
            "/api/payments/momo/sandbox/complete",
            json={"momo_order_id": attempt["momo_order_id"], "result": "approved"},
        )
        assert response.status_code == 503


class TestResults:
    def test_customer_return_confirms_the_order_and_the_ipn_repeats_harmlessly(
        self, shopper, order_id, fake_momo
    ):
        momo_order_id = start(shopper, order_id)["momo_order_id"]
        result = momo_result(momo_order_id)

        returned = shopper.post("/api/payments/momo/return", json=query_string(result))
        assert returned.status_code == 200, returned.text
        assert returned.json()["payment_status"] == "PAID"
        assert returned.json()["status"] == "CONFIRMED"

        # MoMo's own copy arrives later, without a session or CSRF token.
        shopper.headers.pop("X-CSRF-Token")
        shopper.cookies.clear()
        assert shopper.post("/api/payments/momo/ipn", json=result).status_code == 204

    def test_ipn_alone_confirms_the_order(self, shopper, order_id, fake_momo):
        momo_order_id = start(shopper, order_id)["momo_order_id"]

        ipn = shopper.post("/api/payments/momo/ipn", json=momo_result(momo_order_id))
        assert ipn.status_code == 204

        order = shopper.get(f"/api/orders/{order_id}").json()
        assert order["payment_status"] == "PAID"
        assert order["can_pay"] is False

    def test_declined_payment_can_be_retried(self, shopper, order_id, fake_momo):
        momo_order_id = start(shopper, order_id)["momo_order_id"]

        declined = shopper.post(
            "/api/payments/momo/return", json=query_string(momo_result(momo_order_id, 1006))
        )

        assert declined.json()["payment_status"] == "FAILED"
        assert declined.json()["status"] == "PENDING"
        assert start(shopper, order_id)["momo_order_id"] != momo_order_id

    def test_a_pending_result_changes_nothing_until_the_final_one(
        self, shopper, order_id, fake_momo
    ):
        momo_order_id = start(shopper, order_id)["momo_order_id"]

        pending = shopper.post(
            "/api/payments/momo/return", json=query_string(momo_result(momo_order_id, 7000))
        )
        assert pending.json()["payment_status"] == "UNPAID"

        shopper.post("/api/payments/momo/ipn", json=momo_result(momo_order_id))
        assert shopper.get(f"/api/orders/{order_id}").json()["payment_status"] == "PAID"

    @pytest.mark.parametrize(
        "tamper",
        [
            {"resultCode": "0", "signature": "0" * 64},
            {"amount": 1_000},  # signature no longer matches
            {"partnerCode": "SOMEONE_ELSE"},
        ],
    )
    def test_unverifiable_results_are_rejected(self, shopper, order_id, fake_momo, tamper):
        momo_order_id = start(shopper, order_id)["momo_order_id"]
        forged = {**momo_result(momo_order_id), **tamper}

        assert shopper.post("/api/payments/momo/ipn", json=forged).status_code == 400
        returned = shopper.post("/api/payments/momo/return", json=query_string(forged))
        assert returned.status_code == 400
        assert returned.json()["code"] == "invalid_momo_result"
        assert shopper.get(f"/api/orders/{order_id}").json()["payment_status"] == "UNPAID"

    def test_incomplete_results_are_rejected(self, shopper, order_id, fake_momo):
        momo_order_id = start(shopper, order_id)["momo_order_id"]
        incomplete = momo_result(momo_order_id)
        del incomplete["transId"]

        assert shopper.post("/api/payments/momo/ipn", json=incomplete).status_code == 400

    def test_a_signed_amount_other_than_the_total_does_not_pay(self, shopper, order_id, fake_momo):
        momo_order_id = start(shopper, order_id)["momo_order_id"]

        shopper.post("/api/payments/momo/ipn", json=momo_result(momo_order_id, amount=1_000))

        assert shopper.get(f"/api/orders/{order_id}").json()["payment_status"] == "UNPAID"

    def test_retired_attempts_are_not_applied(self, shopper, order_id, fake_momo):
        momo_order_id = start(shopper, order_id)["momo_order_id"]
        shopper.post(f"/api/orders/{order_id}/payments/cod")

        result = momo_result(momo_order_id)
        assert shopper.post("/api/payments/momo/ipn", json=result).status_code == 204
        returned = shopper.post("/api/payments/momo/return", json=query_string(result))
        assert returned.status_code == 404
        assert shopper.get(f"/api/orders/{order_id}").json()["payment_method"] == "COD"

    def test_payment_for_a_cancelled_order_is_not_applied(self, shopper, order_id, fake_momo):
        momo_order_id = start(shopper, order_id)["momo_order_id"]
        shopper.post(f"/api/orders/{order_id}/cancel")

        shopper.post("/api/payments/momo/ipn", json=momo_result(momo_order_id))

        order = shopper.get(f"/api/orders/{order_id}").json()
        assert (order["status"], order["payment_status"]) == ("CANCELLED", "UNPAID")

    def test_results_need_live_keys(self, shopper, order_id, monkeypatch):
        monkeypatch.setattr(get_settings(), "momo_secret_key", "")
        response = shopper.post("/api/payments/momo/ipn", json=momo_result("DATENO_1_x"))
        assert response.status_code == 400
