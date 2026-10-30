from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.admin.schemas import (
    DashboardSummary,
    DishSales,
    MomoStats,
    PaymentStats,
    RatedDish,
    RatingStats,
    RevenueDay,
    RevenueTrend,
    TopDishes,
)
from app.modules.catalog.models import Product
from app.modules.feedback.models import Review
from app.modules.orders.models import Order, OrderItem, OrderStatus, PaymentMethod, PaymentStatus
from app.modules.reservations.models import Reservation, ReservationStatus
from app.modules.reservations.service import restaurant_now
from app.modules.users.models import Role, User


def _window_start(days: int) -> datetime:
    """Start of the restaurant-local day `days - 1` days ago, so `days=7` means this week."""
    today = restaurant_now().date()
    first_day = today - timedelta(days=days - 1)
    return datetime.combine(
        first_day, time.min, tzinfo=ZoneInfo(get_settings().restaurant_timezone)
    )


def summary(db: Session) -> DashboardSummary:
    completed_revenue, completed_orders, total_orders, pending_orders = db.execute(
        select(
            func.coalesce(
                func.sum(case((Order.status == OrderStatus.COMPLETED, Order.total_price))), 0
            ),
            func.count().filter(Order.status == OrderStatus.COMPLETED),
            func.count(),
            func.count().filter(Order.status == OrderStatus.PENDING),
        )
    ).one()
    total_reservations, pending_reservations = db.execute(
        select(
            func.count(), func.count().filter(Reservation.status == ReservationStatus.PENDING)
        ).select_from(Reservation)
    ).one()

    revenue = int(completed_revenue)
    return DashboardSummary(
        completed_revenue=revenue,
        completed_orders=completed_orders,
        average_order_value=round(revenue / completed_orders) if completed_orders else 0,
        total_orders=total_orders,
        pending_orders=pending_orders,
        active_products=db.scalar(
            select(func.count()).select_from(Product).where(Product.deleted_at.is_(None))
        ),
        customers=db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == Role.CUSTOMER, User.deleted_at.is_(None))
        ),
        total_reservations=total_reservations,
        pending_reservations=pending_reservations,
    )


@dataclass(frozen=True)
class DayTotals:
    date: date
    orders: int  # placed that day and not cancelled
    completed: int
    revenue: int  # from the completed ones


def daily_totals(db: Session, first_day: date, last_day: date) -> list[DayTotals]:
    """Orders placed and revenue from completed orders, per restaurant-local day.

    Grouping happens in Python because converting timestamps to a local calendar day is
    dialect-specific SQL; a year of orders is small enough for this to be cheap.
    """
    tz = ZoneInfo(get_settings().restaurant_timezone)
    start = datetime.combine(first_day, time.min, tzinfo=tz)
    end = datetime.combine(last_day + timedelta(days=1), time.min, tzinfo=tz)
    rows = db.execute(
        select(Order.created_at, Order.status, Order.total_price).where(
            Order.created_at >= start, Order.created_at < end, Order.status != OrderStatus.CANCELLED
        )
    ).all()

    orders: dict = defaultdict(int)
    completed: dict = defaultdict(int)
    revenue: dict = defaultdict(int)
    for created_at, status, total in rows:
        day = created_at.astimezone(tz).date()
        orders[day] += 1
        if status == OrderStatus.COMPLETED:
            completed[day] += 1
            revenue[day] += total

    days = (first_day + timedelta(days=offset) for offset in range((last_day - first_day).days + 1))
    return [DayTotals(day, orders[day], completed[day], revenue[day]) for day in days]


def revenue_trend(db: Session, days: int) -> RevenueTrend:
    first_day = _window_start(days).date()
    series = [
        RevenueDay(date=day.date, orders=day.orders, revenue=day.revenue)
        for day in daily_totals(db, first_day, first_day + timedelta(days=days - 1))
    ]
    return RevenueTrend(
        days=series,
        total_orders=sum(day.orders for day in series),
        total_revenue=sum(day.revenue for day in series),
    )


def _sales_query(start: datetime) -> Select:
    # The order join only matches orders inside the window that were not cancelled; items of
    # any other order get a NULL order and are counted as zero rather than filtered out, so
    # dishes with no qualifying sales still appear (with 0) for the "least sold" list.
    counted = Order.id.is_not(None)
    quantity = func.coalesce(func.sum(case((counted, OrderItem.quantity), else_=0)), 0)
    revenue = func.coalesce(
        func.sum(case((counted, OrderItem.price_at_purchase * OrderItem.quantity), else_=0)),
        0,
    )
    return (
        select(
            Product.id,
            Product.name_vi,
            Product.name_en,
            Product.slug,
            quantity.label("qty"),
            revenue.label("rev"),
        )
        .outerjoin(OrderItem, OrderItem.product_id == Product.id)
        .outerjoin(
            Order,
            (Order.id == OrderItem.order_id)
            & (Order.created_at >= start)
            & (Order.status != OrderStatus.CANCELLED),
        )
        .where(Product.deleted_at.is_(None))
        .group_by(Product.id, Product.name_vi, Product.name_en, Product.slug)
    )


def top_dishes(db: Session, days: int, limit: int) -> TopDishes:
    query = _sales_query(_window_start(days)).subquery()

    def fetch(*order_by) -> list[DishSales]:
        return [
            DishSales(
                product_id=r.id,
                name={"vi": r.name_vi, "en": r.name_en},
                slug=r.slug,
                quantity=r.qty,
                revenue=int(r.rev),
            )
            for r in db.execute(select(query).order_by(*order_by).limit(limit))
        ]

    return TopDishes(
        by_quantity=fetch(query.c.qty.desc(), query.c.rev.desc(), query.c.id),
        by_revenue=fetch(query.c.rev.desc(), query.c.qty.desc(), query.c.id),
        least_sold=fetch(query.c.qty.asc(), query.c.rev.asc(), query.c.id),
    )


def payments(db: Session, days: int) -> PaymentStats:
    cod, momo, paid, failed = db.execute(
        select(
            func.count().filter(Order.payment_method == PaymentMethod.COD),
            func.count().filter(Order.payment_method == PaymentMethod.MOMO),
            func.count().filter(
                Order.payment_method == PaymentMethod.MOMO,
                Order.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED]),
            ),
            func.count().filter(
                Order.payment_method == PaymentMethod.MOMO,
                Order.payment_status == PaymentStatus.FAILED,
            ),
        ).where(Order.created_at >= _window_start(days))
    ).one()
    attempts = paid + failed
    return PaymentStats(
        cod_orders=cod,
        momo_orders=momo,
        momo=MomoStats(
            paid=paid,
            failed=failed,
            success_rate=round(paid / attempts, 4) if attempts else None,
        ),
    )


def ratings(db: Session, limit: int) -> RatingStats:
    # The stored average and count leave out reviews staff have hidden.
    lowest = db.execute(
        select(
            Product.id,
            Product.name_vi,
            Product.name_en,
            Product.slug,
            Product.average_rating,
            Product.review_count,
        )
        .where(Product.deleted_at.is_(None), Product.review_count > 0)
        .order_by(Product.average_rating.asc(), Product.review_count.desc(), Product.id)
        .limit(limit)
    ).all()
    latest = db.scalars(
        select(Review).order_by(Review.created_at.desc(), Review.id.desc()).limit(limit)
    ).all()
    return RatingStats(
        lowest_rated=[
            RatedDish(
                product_id=r[0],
                name={"vi": r[1], "en": r[2]},
                slug=r[3],
                average_rating=r[4],
                review_count=r[5],
            )
            for r in lowest
        ],
        latest_reviews=latest,
    )
