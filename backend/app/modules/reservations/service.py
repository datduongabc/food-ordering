from collections.abc import Sequence
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.modules.catalog.models import Location
from app.modules.reservations.models import Reservation, ReservationStatus
from app.modules.reservations.schemas import ReservationIn, ReservationPolicyOut
from app.modules.users.models import User


def restaurant_now() -> datetime:
    """Current wall-clock time at the restaurant; patched in tests to freeze the clock."""
    return utcnow().astimezone(ZoneInfo(get_settings().restaurant_timezone))


def get_policy() -> ReservationPolicyOut:
    settings = get_settings()
    today = restaurant_now().date()
    return ReservationPolicyOut(
        timezone=settings.restaurant_timezone,
        today=today,
        last_bookable_date=today + timedelta(days=settings.reservation_max_days_ahead),
        max_guests=settings.reservation_max_guests,
    )


def _validate_slot(data: ReservationIn) -> None:
    policy = get_policy()
    now = restaurant_now()

    if data.guest_count > policy.max_guests:
        raise BadRequestError(
            f"Online bookings are for up to {policy.max_guests} guests. "
            "Please call the restaurant for larger groups.",
            code="too_many_guests",
            params={"max_guests": policy.max_guests},
        )
    if data.reservation_date < policy.today:
        raise BadRequestError("Reservation date cannot be in the past.", code="date_in_past")
    if data.reservation_date > policy.last_bookable_date:
        days = get_settings().reservation_max_days_ahead
        raise BadRequestError(
            f"Tables can be booked at most {days} days in advance.",
            code="date_too_far",
            params={"days": days},
        )
    if data.reservation_date == policy.today and data.reservation_time <= now.time():
        raise BadRequestError(
            "That time has already passed today. Please pick a later time.", code="time_passed"
        )


def create_reservation(db: Session, user: User | None, data: ReservationIn) -> Reservation:
    _validate_slot(data)
    if db.get(Location, data.location_id) is None:
        raise BadRequestError("Please choose one of our branches.", code="unknown_branch")

    reservation = Reservation(
        # Guests may book without an account; signed-in bookings appear in "My reservations".
        user_id=user.id if user else None,
        **data.model_dump(),
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


def list_my_reservations(db: Session, user: User) -> Sequence[Reservation]:
    return db.scalars(
        select(Reservation)
        .where(Reservation.user_id == user.id)
        .order_by(
            Reservation.reservation_date.desc(),
            Reservation.reservation_time.desc(),
            Reservation.id.desc(),
        )
    ).all()


def cancel_my_reservation(db: Session, user: User, reservation_id: int) -> Reservation:
    reservation = db.scalar(
        select(Reservation)
        .where(Reservation.id == reservation_id, Reservation.user_id == user.id)
        .with_for_update(of=Reservation)
    )
    if reservation is None:
        raise NotFoundError("Reservation not found.", code="reservation_not_found")
    if reservation.status != ReservationStatus.PENDING:
        raise ConflictError(
            "Only pending reservations can be cancelled online.", code="reservation_not_cancellable"
        )
    reservation.status = ReservationStatus.CANCELLED
    reservation.cancelled_at = utcnow()
    db.commit()
    return reservation
