from sqlalchemy import CheckConstraint, ForeignKey, Integer, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.modules.catalog.models import Product


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        # One row per product per user; adding again increments quantity instead.
        UniqueConstraint("user_id", "product_id", name="uq_cart_items_user_product"),
        CheckConstraint("quantity > 0", name="quantity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(SmallInteger, default=1)

    product: Mapped[Product] = relationship(lazy="joined")
