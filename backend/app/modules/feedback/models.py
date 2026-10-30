from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, UTCDateTime
from app.modules.catalog.models import Product
from app.modules.users.models import User


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating"),
        # One review per customer per dish, so a single person cannot skew the average.
        UniqueConstraint("user_id", "product_id", name="uq_reviews_user_product"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[int] = mapped_column(SmallInteger)
    comment: Mapped[str] = mapped_column(Text, default="")
    # Written by someone with a delivered order of the dish. Reviews from before that rule
    # were backfilled from order history.
    verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    # Hidden by staff: off the dish page and out of its rating, but kept for the record.
    hidden_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    # The restaurant's public answer, shown under the review.
    reply: Mapped[str | None] = mapped_column(Text)
    replied_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    user: Mapped[User] = relationship(lazy="joined")
    product: Mapped[Product] = relationship(lazy="joined")
    photos: Mapped[list["ReviewPhoto"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="ReviewPhoto.id",
        lazy="selectin",
    )


class ReviewPhoto(Base):
    """A customer's photo of the dish, stored as WebP under media/reviews with a thumbnail."""

    __tablename__ = "review_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), index=True)
    # Relative to media/reviews.
    path: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())

    review: Mapped[Review] = relationship(back_populates="photos")
