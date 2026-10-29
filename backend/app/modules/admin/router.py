from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile

from app.core.deps import AdminUser, DbSession, require_admin
from app.core.errors import BadRequestError
from app.modules.admin import operations, products, stats, users
from app.modules.admin.products import MAX_IMAGE_BYTES
from app.modules.admin.schemas import (
    AdminOrderOut,
    AdminProductOut,
    AdminReservationOut,
    AdminUserOut,
    DashboardSummary,
    OrderStatusIn,
    Page,
    PaymentStats,
    ProductCreate,
    ProductUpdate,
    RatingStats,
    ReservationStatusIn,
    RevenueTrend,
    TopDishes,
    UserCreate,
    UserUpdate,
)
from app.modules.orders.models import OrderStatus
from app.modules.reservations.models import ReservationStatus

# The dependency on the router guards every route, so a new endpoint cannot forget it.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

PageNo = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]
Days = Annotated[int, Query(ge=1, le=90)]
Limit = Annotated[int, Query(ge=1, le=20)]


# --- Dashboard ---


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(db: DbSession):
    return stats.summary(db)


@router.get("/stats/revenue", response_model=RevenueTrend)
def revenue_trend(db: DbSession, days: Days = 7):
    return stats.revenue_trend(db, days)


@router.get("/stats/top-dishes", response_model=TopDishes)
def top_dishes(db: DbSession, days: Days = 30, limit: Limit = 5):
    return stats.top_dishes(db, days, limit)


@router.get("/stats/payments", response_model=PaymentStats)
def payment_stats(db: DbSession, days: Days = 30):
    return stats.payments(db, days)


@router.get("/stats/ratings", response_model=RatingStats)
def rating_stats(db: DbSession, limit: Limit = 5):
    return stats.ratings(db, limit)


# --- Products ---


@router.get("/products", response_model=list[AdminProductOut])
def list_products(db: DbSession):
    return products.list_products(db)


@router.post("/products", response_model=AdminProductOut, status_code=201)
def create_product(data: ProductCreate, db: DbSession):
    return products.create_product(db, data)


@router.patch("/products/{product_id}", response_model=AdminProductOut)
def update_product(product_id: int, data: ProductUpdate, db: DbSession):
    return products.update_product(db, product_id, data)


@router.put("/products/{product_id}/image", response_model=AdminProductOut)
async def replace_image(product_id: int, image: UploadFile, db: DbSession):
    # Read one byte past the limit so oversized files are rejected without loading them fully.
    data = await image.read(MAX_IMAGE_BYTES + 1)
    if not data:
        raise BadRequestError("The uploaded file is empty.")
    return products.replace_image(db, product_id, data)


@router.post("/products/{product_id}/hide", response_model=AdminProductOut)
def hide_product(product_id: int, db: DbSession):
    return products.hide_product(db, product_id)


@router.post("/products/{product_id}/restore", response_model=AdminProductOut)
def restore_product(product_id: int, db: DbSession):
    return products.restore_product(db, product_id)


# --- Orders ---


@router.get("/orders", response_model=Page[AdminOrderOut])
def list_orders(
    db: DbSession, status: OrderStatus | None = None, page: PageNo = 1, page_size: PageSize = 20
):
    return operations.list_orders(db, status, page, page_size)


@router.get("/orders/{order_id}", response_model=AdminOrderOut)
def get_order(order_id: int, db: DbSession):
    return operations.get_order(db, order_id)


@router.post("/orders/{order_id}/status", response_model=AdminOrderOut)
def change_order_status(order_id: int, data: OrderStatusIn, db: DbSession, admin: AdminUser):
    return operations.change_order_status(db, admin, order_id, data.status, data.note)


# --- Reservations ---


@router.get("/reservations", response_model=Page[AdminReservationOut])
def list_reservations(
    db: DbSession,
    status: ReservationStatus | None = None,
    on_date: Annotated[date | None, Query(alias="date")] = None,
    page: PageNo = 1,
    page_size: PageSize = 20,
):
    return operations.list_reservations(db, status, on_date, page, page_size)


@router.post("/reservations/{reservation_id}/status", response_model=AdminReservationOut)
def change_reservation_status(reservation_id: int, data: ReservationStatusIn, db: DbSession):
    return operations.change_reservation_status(db, reservation_id, data.status)


# --- Users ---


@router.get("/users", response_model=Page[AdminUserOut])
def list_users(
    db: DbSession,
    q: Annotated[str | None, Query(max_length=100)] = None,
    include_deactivated: bool = False,
    page: PageNo = 1,
    page_size: PageSize = 20,
):
    return users.list_users(db, q, include_deactivated, page, page_size)


@router.post("/users", response_model=AdminUserOut, status_code=201)
def create_user(data: UserCreate, db: DbSession):
    return users.create_user(db, data)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(user_id: int, data: UserUpdate, db: DbSession, admin: AdminUser):
    return users.update_user(db, admin, user_id, data)


@router.post("/users/{user_id}/deactivate", response_model=AdminUserOut)
def deactivate_user(user_id: int, db: DbSession, admin: AdminUser):
    return users.deactivate_user(db, admin, user_id)


@router.post("/users/{user_id}/restore", response_model=AdminUserOut)
def restore_user(user_id: int, db: DbSession):
    return users.restore_user(db, user_id)
