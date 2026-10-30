from dataclasses import dataclass
from datetime import date
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.errors import BadRequestError
from app.modules.orders.models import Order, OrderStatus
from app.modules.promotions.models import DiscountKind, PromoCode
from app.modules.users.models import User


def restaurant_today() -> date:
    """Today at the restaurant; patched in tests to freeze the calendar."""
    return utcnow().astimezone(ZoneInfo(get_settings().restaurant_timezone)).date()


def normalize_code(code: str) -> str:
    return code.strip().upper()


def discount_for(promo: PromoCode, subtotal: int) -> int:
    if promo.kind == DiscountKind.PERCENT:
        # Rounded down to whole dong: the customer never pays a fraction, the shop never
        # gives away more than it said.
        discount = subtotal * promo.value // 100
        if promo.max_discount is not None:
            discount = min(discount, promo.max_discount)
    else:
        discount = promo.value
    return min(discount, subtotal)


def count_uses(db: Session, promo_id: int, user_id: int | None = None) -> int:
    query = select(func.count(Order.id)).where(
        Order.promo_code_id == promo_id, Order.status != OrderStatus.CANCELLED
    )
    if user_id is not None:
        query = query.where(Order.user_id == user_id)
    return db.scalar(query) or 0


@dataclass(frozen=True)
class Quote:
    promo: PromoCode
    subtotal: int
    discount: int

    @property
    def total(self) -> int:
        return self.subtotal - self.discount


def quote(db: Session, user: User, code: str, subtotal: int, *, for_update: bool = False) -> Quote:
    """What `code` takes off `subtotal` for this customer now, or why it cannot be used.

    At checkout the code's row is locked, so two last orders cannot both take its final use.
    """
    normalized = normalize_code(code)
    query = select(PromoCode).where(PromoCode.code == normalized)
    if for_update:
        query = query.with_for_update()
    promo = db.scalar(query)
    if promo is None or promo.disabled_at is not None:
        raise BadRequestError(
            f'There is no promo code "{normalized}".',
            code="promo_not_found",
            params={"code": normalized},
        )

    today = restaurant_today()
    if promo.starts_on is not None and today < promo.starts_on:
        raise BadRequestError(
            f"This code can be used from {promo.starts_on.isoformat()}.",
            code="promo_not_started",
            params={"date": promo.starts_on.isoformat()},
        )
    if promo.ends_on is not None and today > promo.ends_on:
        raise BadRequestError(
            f"This code ended on {promo.ends_on.isoformat()}.",
            code="promo_expired",
            params={"date": promo.ends_on.isoformat()},
        )
    if subtotal < promo.min_subtotal:
        raise BadRequestError(
            f"This code needs an order of at least {promo.min_subtotal} VND.",
            code="promo_min_subtotal",
            params={"amount_vnd": promo.min_subtotal},
        )
    if promo.usage_limit is not None and count_uses(db, promo.id) >= promo.usage_limit:
        raise BadRequestError("This code has been fully used.", code="promo_used_up")
    if (
        promo.per_customer_limit is not None
        and count_uses(db, promo.id, user.id) >= promo.per_customer_limit
    ):
        raise BadRequestError(
            "You have already used this code.",
            code="promo_already_used",
            params={"times": promo.per_customer_limit},
        )
    return Quote(promo, subtotal, discount_for(promo, subtotal))
