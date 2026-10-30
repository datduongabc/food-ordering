from datetime import date
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, UploadFile

from app.core.deps import AdminUser, DbSession, require_admin
from app.core.email import Mailer, notify
from app.core.images import MAX_UPLOAD_BYTES
from app.modules.admin import (
    audit,
    exports,
    operations,
    products,
    promotions,
    reviews,
    stats,
    users,
)
from app.modules.admin.schemas import (
    AdminOrderOut,
    AdminProductOut,
    AdminPromoOut,
    AdminReservationOut,
    AdminReviewOut,
    AdminUserOut,
    AuditLogOut,
    DashboardSummary,
    OrderStatusIn,
    Page,
    PaymentStats,
    ProductCreate,
    ProductUpdate,
    PromoCodeIn,
    RatingStats,
    ReservationStatusIn,
    RevenueTrend,
    ReviewReplyIn,
    ReviewVisibility,
    TopDishes,
    UserCreate,
    UserUpdate,
)
from app.modules.notifications import emails
from app.modules.orders.models import OrderStatus
from app.modules.reservations.models import ReservationStatus
from app.modules.users.models import User

# The dependency on the router guards every route, so a new endpoint cannot forget it.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

# Far past the last page of any list; larger numbers would overflow the SQL offset.
PageNo = Annotated[int, Query(ge=1, le=10_000)]
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
def create_product(data: ProductCreate, db: DbSession, admin: AdminUser):
    return products.create_product(db, admin, data)


@router.patch("/products/{product_id}", response_model=AdminProductOut)
def update_product(product_id: int, data: ProductUpdate, db: DbSession, admin: AdminUser):
    return products.update_product(db, admin, product_id, data)


@router.put("/products/{product_id}/image", response_model=AdminProductOut)
async def replace_image(product_id: int, image: UploadFile, db: DbSession, admin: AdminUser):
    # Read one byte past the limit so oversized files are rejected without loading them fully.
    data = await image.read(MAX_UPLOAD_BYTES + 1)
    return products.replace_image(db, admin, product_id, data)


@router.post("/products/{product_id}/hide", response_model=AdminProductOut)
def hide_product(product_id: int, db: DbSession, admin: AdminUser):
    return products.hide_product(db, admin, product_id)


@router.post("/products/{product_id}/restore", response_model=AdminProductOut)
def restore_product(product_id: int, db: DbSession, admin: AdminUser):
    return products.restore_product(db, admin, product_id)


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
def change_order_status(
    order_id: int,
    data: OrderStatusIn,
    db: DbSession,
    admin: AdminUser,
    background: BackgroundTasks,
    mailer: Mailer,
):
    order = operations.change_order_status(db, admin, order_id, data.status, data.note)
    notify(background, mailer, emails.order_status_changed(order))
    return order


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
def change_reservation_status(
    reservation_id: int,
    data: ReservationStatusIn,
    db: DbSession,
    admin: AdminUser,
    background: BackgroundTasks,
    mailer: Mailer,
):
    reservation = operations.change_reservation_status(db, admin, reservation_id, data.status)
    customer = db.get(User, reservation.user_id) if reservation.user_id else None
    if customer is not None:
        notify(
            background,
            mailer,
            emails.reservation_status_changed(reservation, customer.email, by_customer=False),
        )
    return reservation


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
def create_user(data: UserCreate, db: DbSession, admin: AdminUser):
    return users.create_user(db, admin, data)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(user_id: int, data: UserUpdate, db: DbSession, admin: AdminUser):
    return users.update_user(db, admin, user_id, data)


@router.post("/users/{user_id}/deactivate", response_model=AdminUserOut)
def deactivate_user(user_id: int, db: DbSession, admin: AdminUser):
    return users.deactivate_user(db, admin, user_id)


@router.post("/users/{user_id}/restore", response_model=AdminUserOut)
def restore_user(user_id: int, db: DbSession, admin: AdminUser):
    return users.restore_user(db, admin, user_id)


# --- Promo codes ---


@router.get("/promo-codes", response_model=list[AdminPromoOut])
def list_promo_codes(db: DbSession):
    return promotions.list_promos(db)


@router.post("/promo-codes", response_model=AdminPromoOut, status_code=201)
def create_promo_code(data: PromoCodeIn, db: DbSession, admin: AdminUser):
    return promotions.create_promo(db, admin, data)


@router.put("/promo-codes/{promo_id}", response_model=AdminPromoOut)
def update_promo_code(promo_id: int, data: PromoCodeIn, db: DbSession, admin: AdminUser):
    return promotions.update_promo(db, admin, promo_id, data)


@router.post("/promo-codes/{promo_id}/disable", response_model=AdminPromoOut)
def disable_promo_code(promo_id: int, db: DbSession, admin: AdminUser):
    return promotions.disable_promo(db, admin, promo_id)


@router.post("/promo-codes/{promo_id}/enable", response_model=AdminPromoOut)
def enable_promo_code(promo_id: int, db: DbSession, admin: AdminUser):
    return promotions.enable_promo(db, admin, promo_id)


# --- Reviews ---


@router.get("/reviews", response_model=Page[AdminReviewOut])
def list_reviews(
    db: DbSession,
    visibility: ReviewVisibility | None = None,
    rating: Annotated[int | None, Query(ge=1, le=5)] = None,
    product: Annotated[str | None, Query(max_length=120)] = None,
    page: PageNo = 1,
    page_size: PageSize = 20,
):
    return reviews.list_reviews(db, visibility, rating, product, page, page_size)


@router.post("/reviews/{review_id}/hide", response_model=AdminReviewOut)
def hide_review(review_id: int, db: DbSession, admin: AdminUser):
    return reviews.hide_review(db, admin, review_id)


@router.post("/reviews/{review_id}/restore", response_model=AdminReviewOut)
def restore_review(review_id: int, db: DbSession, admin: AdminUser):
    return reviews.restore_review(db, admin, review_id)


@router.put("/reviews/{review_id}/reply", response_model=AdminReviewOut)
def reply_to_review(review_id: int, data: ReviewReplyIn, db: DbSession, admin: AdminUser):
    return reviews.reply_to_review(db, admin, review_id, data.reply)


# --- Reports ---

From = Annotated[date, Query(alias="from")]
To = Annotated[date, Query(alias="to")]


def _download(file: exports.CsvFile) -> Response:
    return Response(
        file.content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
    )


@router.get("/exports/orders.csv", response_class=Response)
def export_orders(
    db: DbSession,
    admin: AdminUser,
    first_day: From,
    last_day: To,
    status: OrderStatus | None = None,
    lang: exports.Lang = "vi",
):
    return _download(exports.orders_csv(db, admin, first_day, last_day, status, lang))


@router.get("/exports/revenue.csv", response_class=Response)
def export_revenue(
    db: DbSession, admin: AdminUser, first_day: From, last_day: To, lang: exports.Lang = "vi"
):
    return _download(exports.revenue_csv(db, admin, first_day, last_day, lang))


# --- Audit log ---


@router.get("/audit-log", response_model=Page[AuditLogOut])
def audit_log(
    db: DbSession,
    action: Annotated[str | None, Query(max_length=50)] = None,
    target_type: Annotated[str | None, Query(max_length=30)] = None,
    target_id: int | None = None,
    page: PageNo = 1,
    page_size: PageSize = 20,
):
    return audit.list_entries(db, action, target_type, target_id, page, page_size)
