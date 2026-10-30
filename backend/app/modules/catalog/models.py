from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    event,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, UTCDateTime
from app.core.localized import LocalizedColumns
from app.core.text import fold

product_availabilities = Table(
    "product_availabilities",
    Base.metadata,
    Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("location_id", ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_vi: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    name = LocalizedColumns("name")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_vi: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[str] = mapped_column(String(255))
    address_vi: Mapped[str] = mapped_column(Text)
    address_en: Mapped[str] = mapped_column(Text)

    name = LocalizedColumns("name")
    address = LocalizedColumns("address")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    image_url: Mapped[str] = mapped_column(String(255))
    name_vi: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[str] = mapped_column(String(255))
    description_vi: Mapped[str] = mapped_column(String(500))
    description_en: Mapped[str] = mapped_column(String(500))
    # Whole Vietnamese dong; VND has no minor unit.
    price: Mapped[int] = mapped_column(BigInteger)
    # Denormalised from reviews so menu sorting by rating needs no aggregate join.
    average_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    # Both names through fold(), kept current on every save, so search needs no accents.
    search_text: Mapped[str] = mapped_column(Text, server_default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    category: Mapped[Category | None] = relationship(lazy="joined")
    # selectin loads every listed product's branches in one extra query instead of one per product.
    locations: Mapped[list[Location]] = relationship(
        secondary=product_availabilities, order_by=Location.id, lazy="selectin"
    )

    name = LocalizedColumns("name")
    description = LocalizedColumns("description")


@event.listens_for(Product, "before_insert")
@event.listens_for(Product, "before_update")
def _refresh_search_text(_mapper, _connection, product: Product) -> None:
    product.search_text = fold(f"{product.name_vi} {product.name_en}")
