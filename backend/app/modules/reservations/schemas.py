from datetime import date, datetime, time
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, computed_field

from app.modules.auth.schemas import Name, Phone
from app.modules.catalog.schemas import LocationOut
from app.modules.reservations.models import ReservationStatus


class ReservationIn(BaseModel):
    location_id: int
    customer_name: Name
    customer_phone: Phone
    reservation_date: date
    reservation_time: time
    # Upper bound is the configurable policy limit, checked in the service.
    guest_count: Annotated[int, Field(ge=1)]
    special_requests: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] = ""


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    location: LocationOut
    customer_name: str
    customer_phone: str
    reservation_date: date
    reservation_time: time
    guest_count: int
    special_requests: str
    status: ReservationStatus
    created_at: datetime
    cancelled_at: datetime | None

    @computed_field
    @property
    def can_cancel(self) -> bool:
        return self.status == ReservationStatus.PENDING


class ReservationPolicyOut(BaseModel):
    """Lets the booking form offer exactly the dates and party sizes the API will accept."""

    timezone: str
    today: date
    last_bookable_date: date
    max_guests: int
    opening_time: time
    last_seating_time: time
