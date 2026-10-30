from datetime import UTC, datetime

import pytest

from app.modules.orders.models import OrderStatus, PaymentMethod, PaymentStatus
from app.modules.orders.schemas import OrderOut


def order(status: OrderStatus, payment_status: PaymentStatus) -> OrderOut:
    return OrderOut(
        id=1,
        status=status,
        payment_method=PaymentMethod.MOMO,
        payment_status=payment_status,
        subtotal_price=100_000,
        discount_amount=0,
        promo_code=None,
        total_price=100_000,
        created_at=datetime(2026, 10, 29, tzinfo=UTC),
        location=None,
        delivery_name="Nguyen Van A",
        delivery_phone="0901234567",
        delivery_address="12 Nguyen Hue",
        delivery_note="",
        items=[],
        events=[],
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
