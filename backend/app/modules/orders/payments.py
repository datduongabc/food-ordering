"""MoMo payment sandbox.

The PHP app never called MoMo; it faked the gateway's signatures in the browser. This keeps
the same customer flow (pay, then approve or decline on a MoMo-style screen) but makes the
simulation explicit and impossible to reach outside local development.
"""

import secrets
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import BadRequestError, ConflictError, NotFoundError, ServiceUnavailableError
from app.modules.orders.models import Order, OrderStatus, PaymentMethod, PaymentStatus
from app.modules.orders.schemas import MomoPaymentOut, SandboxCompleteIn, SandboxResult
from app.modules.orders.service import get_order, transition
from app.modules.users.models import User

# Per-transaction limits of a MoMo wallet payment.
MOMO_MIN_VND = 1_000
MOMO_MAX_VND = 50_000_000


def _require_sandbox() -> None:
    if not get_settings().is_local:
        raise ServiceUnavailableError(
            "MoMo payments are not available yet. Please pay on delivery."
        )


def to_vnd(amount_usd: Decimal, rate: int) -> int:
    return int((amount_usd * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _ensure_payable(order: Order) -> None:
    if order.payment_status == PaymentStatus.PAID:
        raise ConflictError(f"Order #{order.id} has already been paid.")
    if order.status != OrderStatus.PENDING:
        raise ConflictError(f"Order #{order.id} is {order.status.lower()} and cannot be paid.")


def start_momo_payment(db: Session, user: User, order_id: int) -> MomoPaymentOut:
    _require_sandbox()
    order = get_order(db, user, order_id, for_update=True)
    _ensure_payable(order)

    rate = get_settings().momo_usd_to_vnd_rate
    amount_vnd = to_vnd(order.total_price, rate)
    if not MOMO_MIN_VND <= amount_vnd <= MOMO_MAX_VND:
        # The PHP app silently clamped the charge into range; charging a different amount
        # than the order total is worse than refusing.
        raise BadRequestError(
            f"MoMo accepts {MOMO_MIN_VND:,}-{MOMO_MAX_VND:,} VND per payment. "
            "Please choose cash on delivery for this order."
        )

    order.payment_method = PaymentMethod.MOMO
    order.payment_status = PaymentStatus.UNPAID
    # A fresh id per attempt, as MoMo rejects reused order ids after a failed payment.
    order.momo_order_id = f"DATENO_{order.id}_{secrets.token_hex(4)}"
    db.commit()
    return MomoPaymentOut(
        order_id=order.id,
        momo_order_id=order.momo_order_id,
        amount_usd=order.total_price,
        amount_vnd=amount_vnd,
        exchange_rate=rate,
    )


def complete_sandbox_payment(db: Session, user: User, data: SandboxCompleteIn) -> Order:
    _require_sandbox()
    order = db.scalar(
        select(Order)
        .where(Order.momo_order_id == data.momo_order_id, Order.user_id == user.id)
        .with_for_update(of=Order)
    )
    if order is None:
        raise NotFoundError("Payment not found. Start the payment again from your orders.")
    _ensure_payable(order)

    if data.result == SandboxResult.APPROVED:
        order.payment_status = PaymentStatus.PAID
        order.momo_trans_id = f"SANDBOX-{secrets.token_hex(6).upper()}"
        transition(order, OrderStatus.CONFIRMED, None, "MoMo payment received.")
    else:
        order.payment_status = PaymentStatus.FAILED
    db.commit()
    return get_order(db, user, order.id)
