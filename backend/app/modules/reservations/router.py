from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Header, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.deps import CurrentUser, DbSession, OptionalUser
from app.core.email import Mailer, notify
from app.core.events import BrokerDep, EventBroker
from app.core.idempotency import IdempotencyDep
from app.core.rate_limit import BOOKINGS, client_ip, rate_limit
from app.modules.notifications import emails
from app.modules.reservations import service
from app.modules.reservations.schemas import (
    ReservationIn,
    ReservationOut,
    ReservationPolicyOut,
)

router = APIRouter(prefix="/reservations", tags=["reservations"])


def _publish_reservation(broker: EventBroker, reservation) -> dict[str, Any]:
    payload = ReservationOut.model_validate(reservation).model_dump(mode="json")
    broker.publish(f"reservation:{reservation.id}", payload)
    return payload


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
    request: Request,
    data: ReservationIn,
    db: DbSession,
    user: OptionalUser,
    background: BackgroundTasks,
    mailer: Mailer,
    idempotency: IdempotencyDep,
    broker: BrokerDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=128)] = None,
):
    scope = f"reservation:user:{user.id}" if user else f"reservation:ip:{client_ip(request)}"
    cached = idempotency.get(scope, idempotency_key)
    if cached is not None:
        return JSONResponse(cached, status_code=status.HTTP_201_CREATED)
    reservation = service.create_reservation(db, user, data)
    # Guests leave only a phone number, and unverified addresses never receive booking mail.
    if user is not None and user.is_email_verified:
        notify(background, mailer, emails.reservation_received(reservation, user.email))
    payload = _publish_reservation(broker, reservation)
    idempotency.set(scope, idempotency_key, payload)
    return reservation


@router.get("/mine", response_model=list[ReservationOut])
def list_my_reservations(db: DbSession, user: CurrentUser):
    return service.list_my_reservations(db, user)


@router.get("/{reservation_id}/stream")
async def stream_my_reservation(
    reservation_id: int,
    db: DbSession,
    user: CurrentUser,
    broker: BrokerDep,
    once: bool = False,
):
    reservation = service.get_my_reservation(db, user, reservation_id)
    initial = ReservationOut.model_validate(reservation).model_dump(mode="json")
    return StreamingResponse(
        broker.stream(f"reservation:{reservation.id}", initial, once=once),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{reservation_id}/cancel", response_model=ReservationOut)
def cancel_my_reservation(
    reservation_id: int,
    db: DbSession,
    user: CurrentUser,
    background: BackgroundTasks,
    mailer: Mailer,
    broker: BrokerDep,
):
    reservation = service.cancel_my_reservation(db, user, reservation_id)
    if user.is_email_verified:
        notify(
            background,
            mailer,
            emails.reservation_status_changed(reservation, user.email, by_customer=True),
        )
    _publish_reservation(broker, reservation)
    return reservation
