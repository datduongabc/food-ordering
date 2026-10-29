from datetime import date, datetime, time
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, UTCDateTime
from app.modules.catalog.models import Location


class ReservationStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (CheckConstraint("guest_count > 0", name="guest_count"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_phone: Mapped[str] = mapped_column(String(20))
    reservation_date: Mapped[date] = mapped_column(Date)
    reservation_time: Mapped[time] = mapped_column(Time)
    guest_count: Mapped[int] = mapped_column(SmallInteger, default=1)
    special_requests: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, name="reservation_status", native_enum=False, length=20),
        default=ReservationStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    location: Mapped[Location] = relationship(lazy="joined")
