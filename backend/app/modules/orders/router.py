from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Response, status

from app.core.deps import CurrentUser, DbSession
from app.core.errors import BadRequestError, NotFoundError
from app.core.rate_limit import ORDERS, PAYMENTS, rate_limit
from app.modules.orders import payments, service
from app.modules.orders.momo import MomoGateway, MomoResult, get_momo_gateway
from app.modules.orders.schemas import CheckoutIn, MomoPaymentOut, OrderOut, SandboxCompleteIn

router = APIRouter(tags=["orders"])

Gateway = Annotated[MomoGateway | None, Depends(get_momo_gateway)]
MomoParams = Annotated[dict[str, Any], Body()]


def _verified(gateway: MomoGateway | None, params: dict[str, Any]) -> MomoResult:
    result = gateway.parse_result(params) if gateway else None
    if result is None:
        raise BadRequestError(
            "This payment result could not be verified.", code="invalid_momo_result"
        )
    return result


@router.post(
    "/orders",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(ORDERS, per="user")],
)
def place_order(data: CheckoutIn, db: DbSession, user: CurrentUser):
    return service.place_order(db, user, data)


@router.get("/orders", response_model=list[OrderOut])
def list_orders(db: DbSession, user: CurrentUser):
    return service.list_orders(db, user)


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: DbSession, user: CurrentUser):
    return service.get_order(db, user, order_id)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: int, db: DbSession, user: CurrentUser):
    return service.cancel_order(db, user, order_id)


PAYMENT_LIMIT = [rate_limit(PAYMENTS, per="user")]


@router.post(
    "/orders/{order_id}/payments/momo", response_model=MomoPaymentOut, dependencies=PAYMENT_LIMIT
)
def start_momo_payment(order_id: int, db: DbSession, user: CurrentUser, gateway: Gateway):
    return payments.start_momo_payment(db, user, order_id, gateway)


@router.post("/orders/{order_id}/payments/cod", response_model=OrderOut, dependencies=PAYMENT_LIMIT)
def switch_to_cod(order_id: int, db: DbSession, user: CurrentUser):
    return payments.switch_to_cod(db, user, order_id)


@router.post("/payments/momo/sandbox/complete", response_model=OrderOut, dependencies=PAYMENT_LIMIT)
def complete_sandbox_payment(data: SandboxCompleteIn, db: DbSession, user: CurrentUser):
    """Local development only: plays the part of the customer approving in the MoMo app."""
    return payments.complete_sandbox_payment(db, user, data)


@router.post("/payments/momo/return", response_model=OrderOut, dependencies=PAYMENT_LIMIT)
def momo_return(params: MomoParams, db: DbSession, user: CurrentUser, gateway: Gateway):
    """The query string MoMo appends to the redirect URL, forwarded by the SPA. It often
    arrives before the IPN, and is the only report a development machine ever gets."""
    order = payments.apply_momo_result(db, _verified(gateway, params))
    if order is None:
        raise NotFoundError(
            "Payment not found. Start the payment again from your orders.", code="payment_not_found"
        )
    return service.get_order(db, user, order.id)


@router.post("/payments/momo/ipn", status_code=status.HTTP_204_NO_CONTENT)
def momo_ipn(params: MomoParams, db: DbSession, gateway: Gateway):
    """MoMo's server-to-server notification; exempt from CSRF, trusted only by signature."""
    payments.apply_momo_result(db, _verified(gateway, params))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
