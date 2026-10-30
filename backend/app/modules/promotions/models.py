from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import BigInteger, CheckConstraint, Date, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, UTCDateTime


class DiscountKind(StrEnum):
    PERCENT = "PERCENT"
    AMOUNT = "AMOUNT"


class PromoCode(Base):
    """A code customers type at checkout for money off the dishes."""

    __tablename__ = "promo_codes"
    __table_args__ = (CheckConstraint("value > 0", name="value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Stored upper case; customers may type it in any case.
    code: Mapped[str] = mapped_column(String(32), unique=True)
    kind: Mapped[DiscountKind] = mapped_column(
        Enum(DiscountKind, name="discount_kind", native_enum=False, length=20)
    )
    # A percentage (1-100) or whole dong, depending on kind.
    value: Mapped[int] = mapped_column(BigInteger)
    # Caps a percentage discount, so 20% off a banquet does not cost a fortune.
    max_discount: Mapped[int | None] = mapped_column(BigInteger)
    min_subtotal: Mapped[int] = mapped_column(BigInteger, default=0)
    # Restaurant-local days, both inclusive; empty means open-ended.
    starts_on: Mapped[date | None] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    # Orders that may use the code, in total and per customer; cancelled orders give it back.
    usage_limit: Mapped[int | None] = mapped_column(Integer)
    per_customer_limit: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    disabled_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
