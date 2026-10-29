from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession, OptionalUser
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


@router.post("", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(data: ReservationIn, db: DbSession, user: OptionalUser):
    return service.create_reservation(db, user, data)


@router.get("/mine", response_model=list[ReservationOut])
def list_my_reservations(db: DbSession, user: CurrentUser):
    return service.list_my_reservations(db, user)


@router.post("/{reservation_id}/cancel", response_model=ReservationOut)
def cancel_my_reservation(reservation_id: int, db: DbSession, user: CurrentUser):
    return service.cancel_my_reservation(db, user, reservation_id)
