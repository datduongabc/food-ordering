from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import AliasPath, BaseModel, ConfigDict, Field, StringConstraints, computed_field

from app.core.config import get_settings
from app.core.localized import LocalizedText
from app.modules.auth.schemas import Name, Phone
from app.modules.catalog.schemas import LocationOut
from app.modules.orders.models import OrderStatus, PaymentMethod, PaymentStatus

Note = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class CheckoutIn(BaseModel):
    payment_method: PaymentMethod = PaymentMethod.COD
    # Branch that cooks and dispatches the order; every dish must be available there.
    location_id: int
    delivery_name: Name
    delivery_phone: Phone
    delivery_address: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=5, max_length=500)
    ]
    delivery_note: Note = ""


class OrderEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: OrderStatus | None
    to_status: OrderStatus
    note: str
    created_at: datetime


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_name: LocalizedText = Field(validation_alias=AliasPath("product", "name"))
    product_slug: str = Field(validation_alias=AliasPath("product", "slug"))
    image_path: str = Field(validation_alias=AliasPath("product", "image_url"), exclude=True)
    price_at_purchase: int
    quantity: int

    @computed_field
    @property
    def image_url(self) -> str:
        return f"{get_settings().media_url}/products/{self.image_path}"

    @computed_field
    @property
    def subtotal(self) -> int:
        return self.price_at_purchase * self.quantity


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    total_price: int
    created_at: datetime
    location: LocationOut | None
    delivery_name: str | None
    delivery_phone: str | None
    delivery_address: str | None
    delivery_note: str | None
    items: list[OrderItemOut]
    events: list[OrderEventOut]

    @computed_field
    @property
    def can_cancel(self) -> bool:
        return self.status == OrderStatus.PENDING

    @computed_field
    @property
    def can_pay(self) -> bool:
        return self.status == OrderStatus.PENDING and self.payment_status != PaymentStatus.PAID


class SandboxResult(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"


class MomoPaymentOut(BaseModel):
    order_id: int
    momo_order_id: str
    amount: int
    # Only the sandbox exists today; a live MoMo integration would return its payUrl here.
    mode: str = "sandbox"


class SandboxCompleteIn(BaseModel):
    momo_order_id: str
    result: SandboxResult
