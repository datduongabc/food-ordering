"""MoMo payments: the live gateway when keys are configured, otherwise a local sandbox.

The sandbox keeps the customer flow (pay, then approve or decline on a MoMo-style screen)
for development without MoMo keys, and cannot be reached outside local development.
"""

import logging
import secrets
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import BadRequestError, ConflictError, NotFoundError, ServiceUnavailableError
from app.modules.orders.models import Order, OrderStatus, PaymentMethod, PaymentStatus
from app.modules.orders.momo import MomoGateway, MomoResult
from app.modules.orders.schemas import MomoPaymentOut, SandboxCompleteIn, SandboxResult
from app.modules.orders.service import get_order, transition
from app.modules.users.models import User

logger = logging.getLogger(__name__)

# Per-transaction limits of a MoMo wallet payment.
MOMO_MIN_VND = 1_000
MOMO_MAX_VND = 50_000_000


def _require_sandbox() -> None:
    settings = get_settings()
    # With live keys set, a sandbox approval would mark orders paid that MoMo never charged.
    if not settings.is_local or settings.momo_configured:
        raise ServiceUnavailableError(
            "MoMo payments are not available yet. Please pay on delivery.", code="momo_unavailable"
        )


def _ensure_payable(order: Order) -> None:
    if order.payment_status == PaymentStatus.PAID:
        raise ConflictError(
            f"Order #{order.id} has already been paid.",
            code="order_already_paid",
            params={"order_id": order.id},
        )
    if order.status != OrderStatus.PENDING:
        raise ConflictError(
            f"Order #{order.id} is {order.status.lower()} and cannot be paid.",
            code="order_not_payable",
            params={"order_id": order.id, "status": order.status},
        )


def start_momo_payment(
    db: Session, user: User, order_id: int, gateway: MomoGateway | None
) -> MomoPaymentOut:
    if gateway is None:
        _require_sandbox()
    order = get_order(db, user, order_id, for_update=True)
    _ensure_payable(order)

    if not MOMO_MIN_VND <= order.total_price <= MOMO_MAX_VND:
        # The PHP app silently clamped the charge into range; charging a different amount
        # than the order total is worse than refusing.
        raise BadRequestError(
            f"MoMo accepts {MOMO_MIN_VND:,}-{MOMO_MAX_VND:,} VND per payment. "
            "Please choose cash on delivery for this order.",
            code="momo_amount_out_of_range",
            params={"min_vnd": MOMO_MIN_VND, "max_vnd": MOMO_MAX_VND},
        )

    # A fresh id per attempt, as MoMo rejects reused order ids after a failed payment.
    momo_order_id = f"DATENO_{order.id}_{secrets.token_hex(4)}"
    pay_url = None
    if gateway is not None:
        # Before saving: if MoMo is down, the order stays as it was.
        pay_url = gateway.create_payment(
            momo_order_id, order.total_price, f"Thanh toan don hang DaTeNO #{order.id}"
        )
    order.payment_method = PaymentMethod.MOMO
    order.payment_status = PaymentStatus.UNPAID
    order.momo_order_id = momo_order_id
    db.commit()
    return MomoPaymentOut(
        order_id=order.id,
        momo_order_id=momo_order_id,
        amount=order.total_price,
        mode="sandbox" if gateway is None else "gateway",
        pay_url=pay_url,
    )


def switch_to_cod(db: Session, user: User, order_id: int) -> Order:
    """Back to cash on delivery, e.g. after a MoMo payment was declined or abandoned."""
    order = get_order(db, user, order_id, for_update=True)
    _ensure_payable(order)
    order.payment_method = PaymentMethod.COD
    order.payment_status = PaymentStatus.UNPAID
    # Retires the open attempt, so approving it later in a stale tab cannot charge a cash order.
    order.momo_order_id = None
    db.commit()
    return get_order(db, user, order.id)


def complete_sandbox_payment(db: Session, user: User, data: SandboxCompleteIn) -> Order:
    _require_sandbox()
    order = db.scalar(
        select(Order)
        .where(Order.momo_order_id == data.momo_order_id, Order.user_id == user.id)
        .with_for_update(of=Order)
    )
    if order is None:
        raise NotFoundError(
            "Payment not found. Start the payment again from your orders.", code="payment_not_found"
        )
    _ensure_payable(order)

    if data.result == SandboxResult.APPROVED:
        order.payment_status = PaymentStatus.PAID
        order.momo_trans_id = f"SANDBOX-{secrets.token_hex(6).upper()}"
        transition(order, OrderStatus.CONFIRMED, None)
    else:
        order.payment_status = PaymentStatus.FAILED
    db.commit()
    return get_order(db, user, order.id)


@dataclass(frozen=True)
class MomoOutcome:
    order: Order | None  # None when no open attempt has that id
    # Whether this call recorded the result; the IPN and the customer's return both deliver
    # it, and only the first should tell the customer.
    changed: bool = False


def apply_momo_result(db: Session, result: MomoResult) -> MomoOutcome:
    """Records a verified MoMo result. Safe to call twice."""
    order = db.scalar(
        select(Order).where(Order.momo_order_id == result.order_id).with_for_update(of=Order)
    )
    if order is None:
        if result.succeeded:
            # The attempt was replaced (a retry or a switch to cash) yet MoMo still charged.
            logger.error("MoMo charged retired attempt %s; refund it", result.order_id)
        return MomoOutcome(None)
    if order.payment_status == PaymentStatus.PAID or result.pending:
        return MomoOutcome(order)
    if result.amount != order.total_price:
        logger.error(
            "MoMo amount %s for order #%s does not match its total %s",
            result.amount,
            order.id,
            order.total_price,
        )
        return MomoOutcome(order)
    if order.status != OrderStatus.PENDING:
        if result.succeeded:
            logger.error("MoMo charged order #%s, which is %s; refund it", order.id, order.status)
        return MomoOutcome(order)

    if result.succeeded:
        order.payment_status = PaymentStatus.PAID
        order.momo_trans_id = result.trans_id
        transition(order, OrderStatus.CONFIRMED, None)
    else:
        order.payment_status = PaymentStatus.FAILED
    db.commit()
    return MomoOutcome(order, changed=True)
