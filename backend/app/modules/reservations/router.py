from fastapi import APIRouter, BackgroundTasks, status

from app.core.deps import CurrentUser, DbSession, OptionalUser
from app.core.email import Mailer, notify
from app.core.rate_limit import BOOKINGS, rate_limit
from app.modules.notifications import emails
from app.modules.reservations import service
from app.modules.reservations.schemas import (
    ReservationIn,
    ReservationOut,
    ReservationPolicyOut,
)

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("/policy", response_model=ReservationPolicyOut)
def get_policy():
    return service.get_policy()


@router.post(
    "",
    response_model=ReservationOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(BOOKINGS, per="user")],
)
def create_reservation(
    data: ReservationIn,
    db: DbSession,
    user: OptionalUser,
    background: BackgroundTasks,
    mailer: Mailer,
):
    reservation = service.create_reservation(db, user, data)
    # Guests leave only a phone number; the restaurant calls them instead.
    if user is not None:
        notify(background, mailer, emails.reservation_received(reservation, user.email))
    return reservation


@router.get("/mine", response_model=list[ReservationOut])
def list_my_reservations(db: DbSession, user: CurrentUser):
    return service.list_my_reservations(db, user)


@router.post("/{reservation_id}/cancel", response_model=ReservationOut)
def cancel_my_reservation(
    reservation_id: int,
    db: DbSession,
    user: CurrentUser,
    background: BackgroundTasks,
    mailer: Mailer,
):
    reservation = service.cancel_my_reservation(db, user, reservation_id)
    notify(
        background,
        mailer,
        emails.reservation_status_changed(reservation, user.email, by_customer=True),
    )
    return reservation
