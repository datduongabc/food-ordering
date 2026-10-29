from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.modules.orders.models import OrderStatus, PaymentMethod, PaymentStatus
from app.modules.orders.payments import to_vnd
from app.modules.orders.schemas import OrderOut


@pytest.mark.parametrize(
    ("usd", "vnd"),
    [
        (Decimal("59.00"), 1_475_000),
        (Decimal("0.04"), 1_000),
        (Decimal("12.34"), 308_500),
        # Half a dong rounds up, never truncates the charge.
        (Decimal("0.00002"), 1),
    ],
)
def test_to_vnd(usd, vnd):
    assert to_vnd(usd, 25_000) == vnd


def order(status: OrderStatus, payment_status: PaymentStatus) -> OrderOut:
    return OrderOut(
        id=1,
        status=status,
        payment_method=PaymentMethod.MOMO,
        payment_status=payment_status,
        total_price=Decimal("10.00"),
        created_at=datetime(2026, 10, 29, tzinfo=UTC),
        items=[],
    )


@pytest.mark.parametrize(
    ("status", "payment_status", "can_cancel", "can_pay"),
    [
        (OrderStatus.PENDING, PaymentStatus.UNPAID, True, True),
        (OrderStatus.PENDING, PaymentStatus.FAILED, True, True),
        (OrderStatus.CONFIRMED, PaymentStatus.PAID, False, False),
        (OrderStatus.CONFIRMED, PaymentStatus.UNPAID, False, False),
        (OrderStatus.CANCELLED, PaymentStatus.UNPAID, False, False),
        (OrderStatus.COMPLETED, PaymentStatus.PAID, False, False),
    ],
)
def test_order_actions_follow_status(status, payment_status, can_cancel, can_pay):
    out = order(status, payment_status)
    assert (out.can_cancel, out.can_pay) == (can_cancel, can_pay)
