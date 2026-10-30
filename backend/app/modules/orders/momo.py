"""MoMo wallet gateway (API v2, "captureWallet").

The customer is sent to MoMo's payUrl and approves there. MoMo then reports the result twice:
to the IPN endpoint server-to-server, and through the browser on its way back to the
redirect URL. Both carry the same HMAC-SHA256 signature, which is the only reason to trust
them; anyone can call either endpoint.
"""

import hashlib
import hmac
import json
import logging
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from app.core.config import Settings, get_settings
from app.core.errors import ServiceUnavailableError

logger = logging.getLogger(__name__)

CREATE_PATH = "/v2/gateway/api/create"
# MoMo answers within 30 seconds or treats the request as failed.
TIMEOUT_SECONDS = 30

PENDING_CODES = frozenset({1000, 7000, 7002})

# Fields of a result notification, in the order MoMo signs them.
RESULT_FIELDS = (
    "accessKey",
    "amount",
    "extraData",
    "message",
    "orderId",
    "orderInfo",
    "orderType",
    "partnerCode",
    "payType",
    "requestId",
    "responseTime",
    "resultCode",
    "transId",
)


@dataclass(frozen=True)
class MomoResult:
    order_id: str
    amount: int
    result_code: int
    trans_id: str

    @property
    def succeeded(self) -> bool:
        return self.result_code == 0

    @property
    def pending(self) -> bool:
        # Awaiting the customer's confirmation or still processing; a final result follows.
        return self.result_code in PENDING_CODES


class MomoGateway(Protocol):
    def create_payment(self, order_id: str, amount: int, order_info: str) -> str:
        """Registers a payment and returns the payUrl to send the customer to."""
        ...

    def parse_result(self, params: Mapping[str, object]) -> MomoResult | None:
        """The verified result, or None when the signature or partner does not match."""
        ...


def sign(secret_key: str, fields: Mapping[str, object]) -> str:
    raw = "&".join(f"{name}={fields[name]}" for name in sorted(fields))
    return hmac.new(secret_key.encode(), raw.encode(), hashlib.sha256).hexdigest()


class HttpMomoGateway:
    def __init__(self, settings: Settings):
        self._settings = settings

    def create_payment(self, order_id: str, amount: int, order_info: str) -> str:
        s = self._settings
        site = s.public_url.rstrip("/")
        fields = {
            "accessKey": s.momo_access_key,
            "amount": amount,
            "extraData": "",
            "ipnUrl": f"{site}/api/payments/momo/ipn",
            "orderId": order_id,
            "orderInfo": order_info,
            "partnerCode": s.momo_partner_code,
            "redirectUrl": f"{site}/payment/momo/return",
            # One request per attempt, so the attempt's id doubles as the request id.
            "requestId": order_id,
            "requestType": "captureWallet",
        }
        body = {k: v for k, v in fields.items() if k != "accessKey"}
        body |= {"lang": "vi", "signature": sign(s.momo_secret_key, fields)}

        request = urllib.request.Request(
            s.momo_endpoint + CREATE_PATH,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                answer = json.load(response)
        except urllib.error.HTTPError as exc:
            # MoMo reports refusals as HTTP errors with its resultCode in the body.
            logger.warning("MoMo refused %s: HTTP %s %s", order_id, exc.code, exc.read()[:500])
            raise _unavailable() from exc
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            logger.warning("MoMo create failed for %s: %s", order_id, exc)
            raise _unavailable() from exc

        if answer.get("resultCode") != 0 or not answer.get("payUrl"):
            logger.warning(
                "MoMo refused %s: %s %s", order_id, answer.get("resultCode"), answer.get("message")
            )
            raise _unavailable()
        return answer["payUrl"]

    def parse_result(self, params: Mapping[str, object]) -> MomoResult | None:
        s = self._settings
        try:
            fields = {name: params[name] for name in RESULT_FIELDS if name != "accessKey"}
            signature = str(params["signature"])
            result = MomoResult(
                order_id=str(fields["orderId"]),
                amount=int(str(fields["amount"])),
                result_code=int(str(fields["resultCode"])),
                trans_id=str(fields["transId"]),
            )
        except (KeyError, ValueError):
            return None
        expected = sign(s.momo_secret_key, {"accessKey": s.momo_access_key, **fields})
        if fields["partnerCode"] != s.momo_partner_code or not hmac.compare_digest(
            expected, signature
        ):
            return None
        return result


def _unavailable() -> ServiceUnavailableError:
    return ServiceUnavailableError(
        "MoMo is not responding. Please try again in a moment or pay on delivery.",
        code="momo_unreachable",
    )


def get_momo_gateway() -> MomoGateway | None:
    """The live gateway when MoMo keys are set; None means the local sandbox (or nothing)."""
    settings = get_settings()
    return HttpMomoGateway(settings) if settings.momo_configured else None
