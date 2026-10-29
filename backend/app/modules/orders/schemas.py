from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import AliasPath, BaseModel, ConfigDict, Field, computed_field

from app.core.config import get_settings
from app.modules.orders.models import OrderStatus, PaymentMethod, PaymentStatus


class CheckoutIn(BaseModel):
    payment_method: PaymentMethod = PaymentMethod.COD


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_name: str = Field(validation_alias=AliasPath("product", "name"))
    product_slug: str = Field(validation_alias=AliasPath("product", "slug"))
    image_path: str = Field(validation_alias=AliasPath("product", "image_url"), exclude=True)
    price_at_purchase: Decimal
    quantity: int

    @computed_field
    @property
    def image_url(self) -> str:
        return f"{get_settings().media_url}/products/{self.image_path}"

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        return self.price_at_purchase * self.quantity


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    total_price: Decimal
    created_at: datetime
    items: list[OrderItemOut]

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
    amount_usd: Decimal
    amount_vnd: int
    exchange_rate: int
    # Only the sandbox exists today; a live MoMo integration would return its payUrl here.
    mode: str = "sandbox"


class SandboxCompleteIn(BaseModel):
    momo_order_id: str
    result: SandboxResult
