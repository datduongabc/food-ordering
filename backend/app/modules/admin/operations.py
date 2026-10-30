"""Staff handling of orders and reservations: browsing, filtering and moving them along."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import utcnow
from app.core.errors import ConflictError, NotFoundError
from app.modules.admin import audit
from app.modules.admin.pagination import paginate
from app.modules.admin.schemas import Page
from app.modules.orders.models import Order, OrderStatus
from app.modules.orders.service import transition
from app.modules.reservations.models import Reservation, ReservationStatus
from app.modules.users.models import User

RESERVATION_TRANSITIONS: dict[ReservationStatus, frozenset[ReservationStatus]] = {
    ReservationStatus.PENDING: frozenset(
        {ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED}
    ),
    ReservationStatus.CONFIRMED: frozenset(
        {ReservationStatus.COMPLETED, ReservationStatus.CANCELLED}
    ),
    ReservationStatus.COMPLETED: frozenset(),
    ReservationStatus.CANCELLED: frozenset(),
}


def list_orders(db: Session, status: OrderStatus | None, page: int, page_size: int) -> Page[Order]:
    query = select(Order).order_by(Order.created_at.desc(), Order.id.desc())
    if status is not None:
        query = query.where(Order.status == status)
    return paginate(db, query, page, page_size)


def get_order(db: Session, order_id: int, *, for_update: bool = False) -> Order:
    query = select(Order).where(Order.id == order_id)
    if for_update:
        query = query.with_for_update(of=Order)
    order = db.scalar(query)
    if order is None:
        raise NotFoundError("Order not found.", code="order_not_found")
    return order


def change_order_status(
    db: Session, admin: User, order_id: int, status: OrderStatus, note: str
) -> Order:
    order = get_order(db, order_id, for_update=True)
    before = order.status
    transition(order, status, admin, note)
    changes: dict = {"status": [before, status]}
    if note:
        changes["note"] = [None, note]
    audit.record(db, admin, "order.status", "order", order.id, f"#{order.id}", changes)
    db.commit()
    return order


def list_reservations(
    db: Session,
    status: ReservationStatus | None,
    on_date: date | None,
    page: int,
    page_size: int,
) -> Page[Reservation]:
    # Soonest first: staff care about who is arriving next, not who booked last.
    query = select(Reservation).order_by(
        Reservation.reservation_date, Reservation.reservation_time, Reservation.id
    )
    if status is not None:
        query = query.where(Reservation.status == status)
    if on_date is not None:
        query = query.where(Reservation.reservation_date == on_date)
    return paginate(db, query, page, page_size)


def change_reservation_status(
    db: Session, admin: User, reservation_id: int, status: ReservationStatus
) -> Reservation:
    reservation = db.scalar(
        select(Reservation).where(Reservation.id == reservation_id).with_for_update(of=Reservation)
    )
    if reservation is None:
        raise NotFoundError("Reservation not found.", code="reservation_not_found")
    if status not in RESERVATION_TRANSITIONS[reservation.status]:
        raise ConflictError(
            f"Reservation #{reservation.id} is {reservation.status.lower()} "
            f"and cannot become {status.lower()}.",
            code="invalid_status_transition",
            params={"from": reservation.status, "to": status},
        )
    audit.record(
        db,
        admin,
        "reservation.status",
        "reservation",
        reservation.id,
        f"#{reservation.id} {reservation.customer_name}",
        {"status": [reservation.status, status]},
    )
    reservation.status = status
    if status == ReservationStatus.CANCELLED:
        reservation.cancelled_at = utcnow()
    db.commit()
    return reservation
