"""CSV reports for staff: orders and daily revenue over a date range.

Files start with a UTF-8 byte order mark so Excel shows Vietnamese correctly, and every
export is written to the audit log, since the orders file holds customers' contact details.
"""

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.errors import BadRequestError
from app.modules.admin import audit
from app.modules.admin.stats import daily_totals
from app.modules.orders.models import Order, OrderStatus, PaymentMethod, PaymentStatus
from app.modules.users.models import User

Lang = Literal["vi", "en"]
MAX_DAYS = 366

# Spreadsheets run a cell starting with one of these as a formula, and customers type
# their own names and addresses; a leading quote keeps such a cell plain text.
FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")

ORDER_HEADERS = {
    "vi": [
        "Mã đơn",
        "Thời gian đặt",
        "Khách hàng",
        "Email",
        "Người nhận",
        "SĐT nhận",
        "Địa chỉ giao",
        "Chi nhánh",
        "Số món",
        "Tổng tiền (VND)",
        "Trạng thái",
        "Hình thức thanh toán",
        "Tình trạng thanh toán",
        "Mã giao dịch MoMo",
    ],
    "en": [
        "Order",
        "Placed at",
        "Customer",
        "Email",
        "Recipient",
        "Recipient phone",
        "Delivery address",
        "Branch",
        "Items",
        "Total (VND)",
        "Status",
        "Payment method",
        "Payment status",
        "MoMo transaction",
    ],
}
REVENUE_HEADERS = {
    "vi": ["Ngày", "Đơn đã đặt", "Đơn hoàn thành", "Doanh thu (VND)"],
    "en": ["Date", "Orders placed", "Orders completed", "Revenue (VND)"],
}
LABELS: dict[Lang, dict[str, str]] = {
    "vi": {
        OrderStatus.PENDING: "Chờ xác nhận",
        OrderStatus.CONFIRMED: "Đã xác nhận",
        OrderStatus.COMPLETED: "Hoàn thành",
        OrderStatus.CANCELLED: "Đã hủy",
        PaymentMethod.COD: "Tiền mặt khi nhận hàng",
        PaymentMethod.MOMO: "Ví MoMo",
        PaymentStatus.UNPAID: "Chưa thanh toán",
        PaymentStatus.PAID: "Đã thanh toán",
        PaymentStatus.FAILED: "Thanh toán thất bại",
        PaymentStatus.REFUNDED: "Đã hoàn tiền",
    },
    "en": {
        OrderStatus.PENDING: "Pending",
        OrderStatus.CONFIRMED: "Confirmed",
        OrderStatus.COMPLETED: "Completed",
        OrderStatus.CANCELLED: "Cancelled",
        PaymentMethod.COD: "Cash on delivery",
        PaymentMethod.MOMO: "MoMo wallet",
        PaymentStatus.UNPAID: "Unpaid",
        PaymentStatus.PAID: "Paid",
        PaymentStatus.FAILED: "Failed",
        PaymentStatus.REFUNDED: "Refunded",
    },
}


@dataclass(frozen=True)
class CsvFile:
    filename: str
    content: str


def check_range(first_day: date, last_day: date) -> None:
    if last_day < first_day or (last_day - first_day).days >= MAX_DAYS:
        raise BadRequestError(
            f"Choose an end date on or after the start date, at most {MAX_DAYS} days later.",
            code="invalid_date_range",
            params={"max_days": MAX_DAYS},
        )


def _cell(value: object) -> object:
    if isinstance(value, str) and value.startswith(FORMULA_STARTS):
        return "'" + value
    return value


def _csv(rows: list[list[object]]) -> str:
    buffer = io.StringIO()
    buffer.write("﻿")
    writer = csv.writer(buffer)
    writer.writerows([[_cell(value) for value in row] for row in rows])
    return buffer.getvalue()


def _span(first_day: date, last_day: date) -> str:
    return f"{first_day.isoformat()}_{last_day.isoformat()}"


def _audit(db: Session, admin: User, report: str, first_day, last_day, rows: int, **filters):
    details = {"from": first_day.isoformat(), "to": last_day.isoformat(), **filters, "rows": rows}
    audit.record(
        db,
        admin,
        f"export.{report}",
        "export",
        None,
        f"{first_day.isoformat()} → {last_day.isoformat()}",
        audit.created({key: value for key, value in details.items() if value is not None}),
    )
    db.commit()


def orders_csv(
    db: Session,
    admin: User,
    first_day: date,
    last_day: date,
    status: OrderStatus | None,
    lang: Lang,
) -> CsvFile:
    check_range(first_day, last_day)
    tz = ZoneInfo(get_settings().restaurant_timezone)
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .where(
            Order.created_at >= datetime.combine(first_day, time.min, tzinfo=tz),
            Order.created_at < datetime.combine(last_day + timedelta(days=1), time.min, tzinfo=tz),
        )
        .order_by(Order.created_at, Order.id)
    )
    if status is not None:
        query = query.where(Order.status == status)
    orders = db.scalars(query).unique().all()

    labels = LABELS[lang]
    rows: list[list[object]] = [ORDER_HEADERS[lang]]
    for order in orders:
        rows.append(
            [
                order.id,
                order.created_at.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
                order.user.name,
                order.user.email,
                order.delivery_name or "",
                order.delivery_phone or "",
                order.delivery_address or "",
                order.location.name[lang] if order.location else "",
                sum(item.quantity for item in order.items),
                order.total_price,
                labels[order.status],
                labels[order.payment_method],
                labels[order.payment_status],
                order.momo_trans_id or "",
            ]
        )
    _audit(db, admin, "orders", first_day, last_day, len(orders), status=status)
    suffix = f"-{status.lower()}" if status else ""
    return CsvFile(f"dateno-orders-{_span(first_day, last_day)}{suffix}.csv", _csv(rows))


def revenue_csv(db: Session, admin: User, first_day: date, last_day: date, lang: Lang) -> CsvFile:
    check_range(first_day, last_day)
    days = daily_totals(db, first_day, last_day)
    rows: list[list[object]] = [REVENUE_HEADERS[lang]]
    rows += [[day.date.isoformat(), day.orders, day.completed, day.revenue] for day in days]
    total = "Tổng" if lang == "vi" else "Total"
    rows.append(
        [
            total,
            sum(day.orders for day in days),
            sum(day.completed for day in days),
            sum(day.revenue for day in days),
        ]
    )
    _audit(db, admin, "revenue", first_day, last_day, len(days))
    return CsvFile(f"dateno-revenue-{_span(first_day, last_day)}.csv", _csv(rows))
