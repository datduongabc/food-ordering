from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import AliasPath, BaseModel, ConfigDict, Field, StringConstraints

from app.modules.auth.schemas import Name, NormalizedEmail, Password, Phone
from app.modules.catalog.schemas import ProductOut
from app.modules.orders.models import OrderStatus
from app.modules.orders.schemas import Note, OrderEventOut, OrderOut
from app.modules.reservations.models import ReservationStatus
from app.modules.reservations.schemas import ReservationOut
from app.modules.users.models import Role


class Page[T](BaseModel):
    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int


# --- Dashboard and statistics ---------------------------------------------------------


class DashboardSummary(BaseModel):
    completed_revenue: Decimal
    completed_orders: int
    average_order_value: Decimal
    total_orders: int
    pending_orders: int
    active_products: int
    customers: int
    total_reservations: int
    pending_reservations: int


class RevenueDay(BaseModel):
    date: date
    orders: int
    revenue: Decimal


class RevenueTrend(BaseModel):
    days: list[RevenueDay]
    total_orders: int
    total_revenue: Decimal


class DishSales(BaseModel):
    product_id: int
    name: str
    slug: str
    quantity: int
    revenue: Decimal


class TopDishes(BaseModel):
    by_quantity: list[DishSales]
    by_revenue: list[DishSales]
    least_sold: list[DishSales]


class MomoStats(BaseModel):
    paid: int
    failed: int
    success_rate: float | None


class PaymentStats(BaseModel):
    cod_orders: int
    momo_orders: int
    momo: MomoStats


class RatedDish(BaseModel):
    product_id: int
    name: str
    slug: str
    average_rating: Decimal
    review_count: int


class AdminReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rating: int
    comment: str
    created_at: datetime
    user_name: str = Field(validation_alias=AliasPath("user", "name"))
    product_name: str = Field(validation_alias=AliasPath("product", "name"))
    product_slug: str = Field(validation_alias=AliasPath("product", "slug"))


class RatingStats(BaseModel):
    lowest_rated: list[RatedDish]
    latest_reviews: list[AdminReviewOut]


# --- Products ---------------------------------------------------------------------------

Price = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Slug = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=255),
]


class AdminProductOut(ProductOut):
    created_at: datetime
    deleted_at: datetime | None


class ProductCreate(BaseModel):
    name: Name
    slug: Slug | None = None
    description: Description
    price: Price
    category_id: int
    location_ids: Annotated[list[int], Field(min_length=1)]


class ProductUpdate(BaseModel):
    name: Name | None = None
    slug: Slug | None = None
    description: Description | None = None
    price: Price | None = None
    category_id: int | None = None
    location_ids: Annotated[list[int], Field(min_length=1)] | None = None


# --- Orders -----------------------------------------------------------------------------


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: str


class AdminOrderEventOut(OrderEventOut):
    actor_name: str | None = Field(validation_alias=AliasPath("actor", "name"), default=None)


class AdminOrderOut(OrderOut):
    customer: CustomerOut = Field(validation_alias="user")
    momo_order_id: str | None
    momo_trans_id: str | None
    events: list[AdminOrderEventOut]


class OrderStatusIn(BaseModel):
    status: OrderStatus
    note: Note = ""


# --- Reservations -----------------------------------------------------------------------


class AdminReservationOut(ReservationOut):
    user_id: int | None


class ReservationStatusIn(BaseModel):
    status: ReservationStatus


# --- Users ------------------------------------------------------------------------------


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: str
    role: Role
    is_email_verified: bool
    created_at: datetime
    deleted_at: datetime | None


class UserCreate(BaseModel):
    name: Name
    email: NormalizedEmail
    phone: Phone
    password: Password
    role: Role = Role.CUSTOMER
    email_verified: bool = False


class UserUpdate(BaseModel):
    name: Name | None = None
    email: NormalizedEmail | None = None
    phone: Phone | None = None
    role: Role | None = None
    email_verified: bool | None = None
    # Lets staff set a new password for a customer who cannot receive email.
    password: Password | None = None
