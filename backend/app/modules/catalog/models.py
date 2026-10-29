from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, UTCDateTime

product_availabilities = Table(
    "product_availabilities",
    Base.metadata,
    Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("location_id", ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(Text)
    map_url: Mapped[str] = mapped_column(Text)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    image_url: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(500))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # Denormalised from reviews so menu sorting by rating needs no aggregate join.
    average_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    category: Mapped[Category | None] = relationship(lazy="joined")
    locations: Mapped[list[Location]] = relationship(
        secondary=product_availabilities, order_by=Location.id
    )
