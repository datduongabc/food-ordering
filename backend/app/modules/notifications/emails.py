"""Emails telling customers what happened to their orders and table bookings.

Accounts do not store a language, so each email carries Vietnamese first and English
below. Builders return None when there is nothing worth telling (or nobody to tell), so
callers can hand the result straight to the mailer.
"""

from datetime import date, time

from app.core.config import get_settings
from app.core.email import Email
from app.modules.orders.models import Order, OrderStatus, PaymentMethod, PaymentStatus
from app.modules.reservations.models import Reservation, ReservationStatus

DIVIDER = "\n\n----------------------------------------\nEnglish version\n\n"
SIGNATURE = {"vi": "Nhà hàng DaTeNO", "en": "DaTeNO Restaurant"}
WEEKDAYS = {
    "vi": ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}
PAYMENT = {
    "vi": {
        PaymentMethod.COD: "Tiền mặt khi nhận hàng",
        PaymentMethod.MOMO: "Ví MoMo",
    },
    "en": {
        PaymentMethod.COD: "Cash on delivery",
        PaymentMethod.MOMO: "MoMo wallet",
    },
}


def vnd(amount: int) -> str:
    return f"{amount:,}".replace(",", ".") + " ₫"


def _when(day: date, at: time, lang: str) -> str:
    clock = at.strftime("%H:%M")
    if lang == "vi":
        return f"{WEEKDAYS['vi'][day.weekday()]}, {day:%d/%m/%Y} lúc {clock}"
    return f"{WEEKDAYS['en'][day.weekday()]} {day.day} {day:%B %Y} at {clock}"


def _link(path: str) -> str:
    return get_settings().public_url.rstrip("/") + path


def _bilingual(to: str, subject: tuple[str, str], vi: list[str], en: list[str]) -> Email:
    body_vi = "\n".join([*vi, "", SIGNATURE["vi"]])
    body_en = "\n".join([*en, "", SIGNATURE["en"]])
    return Email(to=to, subject=f"{subject[0]} / {subject[1]}", text=body_vi + DIVIDER + body_en)


# --- Orders ---------------------------------------------------------------------------


def _order_summary(order: Order, lang: str) -> list[str]:
    lines = []
    for item in order.items:
        subtotal = vnd(item.price_at_purchase * item.quantity)
        lines.append(f"  {item.quantity} x {item.product.name[lang]}: {subtotal}")
    if order.discount_amount:
        subtotal = "Tạm tính" if lang == "vi" else "Subtotal"
        discount = "Giảm giá" if lang == "vi" else "Discount"
        lines += [
            f"{subtotal}: {vnd(order.subtotal_price)}",
            f"{discount} ({order.promo_code}): -{vnd(order.discount_amount)}",
        ]
    total = "Tổng cộng" if lang == "vi" else "Total"
    payment = "Thanh toán" if lang == "vi" else "Payment"
    deliver = "Giao tới" if lang == "vi" else "Deliver to"
    branch = "Chi nhánh" if lang == "vi" else "Branch"
    lines += [
        f"{total}: {vnd(order.total_price)}",
        f"{payment}: {PAYMENT[lang][order.payment_method]}",
        f"{deliver}: {order.delivery_name}, {order.delivery_phone}, {order.delivery_address}",
    ]
    if order.location:
        lines.append(f"{branch}: {order.location.name[lang]}")
    return lines


def order_placed(order: Order) -> Email:
    n = order.id
    link = _link(f"/account?order={n}")
    momo = order.payment_method == PaymentMethod.MOMO
    return _bilingual(
        order.user.email,
        (f"DaTeNO: Đã nhận đơn hàng #{n}", f"Order #{n} received"),
        [
            f"Chào {order.user.name},",
            "",
            f"DaTeNO đã nhận đơn hàng #{n} của quý khách:",
            *_order_summary(order, "vi"),
            "",
            "Đơn hàng sẽ được xác nhận ngay khi quý khách hoàn tất thanh toán MoMo."
            if momo
            else "Nhà hàng sẽ gọi xác nhận và bắt đầu chuẩn bị món trong ít phút.",
            f"Theo dõi đơn hàng: {link}",
        ],
        [
            f"Hello {order.user.name},",
            "",
            f"We have received your order #{n}:",
            *_order_summary(order, "en"),
            "",
            "We will confirm it as soon as your MoMo payment goes through."
            if momo
            else "We will confirm it and start cooking within a few minutes.",
            f"Track your order: {link}",
        ],
    )


def order_status_changed(order: Order) -> Email | None:
    """The latest status change, as told to the customer; None when it needs no email."""
    event = order.events[-1]
    n = order.id
    link = _link(f"/account?order={n}")
    note_vi = [f"Lời nhắn từ nhà hàng: {event.note}"] if event.note else []
    note_en = [f"Message from the restaurant: {event.note}"] if event.note else []

    if event.to_status == OrderStatus.CONFIRMED:
        paid = (
            order.payment_status == PaymentStatus.PAID
            and order.payment_method == PaymentMethod.MOMO
        )
        subject = (
            (f"DaTeNO: Đã nhận thanh toán đơn #{n}", f"Payment received for order #{n}")
            if paid
            else (f"DaTeNO: Đơn hàng #{n} đã được xác nhận", f"Order #{n} confirmed")
        )
        vi = [
            f"Đã nhận {vnd(order.total_price)} qua ví MoMo cho đơn hàng #{n}." if paid else "",
            f"Nhà hàng đã xác nhận đơn hàng #{n} và đang chuẩn bị món.",
        ]
        en = [
            f"We received {vnd(order.total_price)} by MoMo for order #{n}." if paid else "",
            f"Your order #{n} is confirmed and the kitchen is on it.",
        ]
    elif event.to_status == OrderStatus.COMPLETED:
        subject = (f"DaTeNO: Đơn hàng #{n} đã giao xong", f"Order #{n} delivered")
        vi = [f"Đơn hàng #{n} đã được giao. Cảm ơn quý khách đã chọn DaTeNO, chúc ngon miệng!"]
        en = [f"Your order #{n} has been delivered. Thank you for choosing DaTeNO, enjoy!"]
    elif event.to_status == OrderStatus.CANCELLED:
        by_customer = event.actor_id == order.user_id
        refund = order.payment_status == PaymentStatus.REFUNDED
        subject = (f"DaTeNO: Đơn hàng #{n} đã hủy", f"Order #{n} cancelled")
        vi = [
            f"Quý khách đã hủy đơn hàng #{n}."
            if by_customer
            else f"Rất tiếc, nhà hàng đã phải hủy đơn hàng #{n}.",
            "Khoản thanh toán MoMo sẽ được hoàn lại vào ví của quý khách." if refund else "",
        ]
        en = [
            f"You cancelled order #{n}." if by_customer else f"Sorry, we had to cancel order #{n}.",
            "Your MoMo payment will be refunded to your wallet." if refund else "",
        ]
    else:
        return None

    return _bilingual(
        order.user.email,
        subject,
        [f"Chào {order.user.name},", "", *filter(None, vi), *note_vi, "", f"Chi tiết: {link}"],
        [f"Hello {order.user.name},", "", *filter(None, en), *note_en, "", f"Details: {link}"],
    )


# --- Table bookings -------------------------------------------------------------------


def _booking_summary(reservation: Reservation, lang: str) -> list[str]:
    when = _when(reservation.reservation_date, reservation.reservation_time, lang)
    if lang == "vi":
        lines = [
            f"  Thời gian: {when}",
            f"  Số khách: {reservation.guest_count}",
            f"  Chi nhánh: {reservation.location.name['vi']}, {reservation.location.address['vi']}",
        ]
        if reservation.special_requests:
            lines.append(f"  Yêu cầu: {reservation.special_requests}")
    else:
        lines = [
            f"  When: {when}",
            f"  Guests: {reservation.guest_count}",
            f"  Branch: {reservation.location.name['en']}, {reservation.location.address['en']}",
        ]
        if reservation.special_requests:
            lines.append(f"  Requests: {reservation.special_requests}")
    return lines


def reservation_received(reservation: Reservation, to: str) -> Email:
    n = reservation.id
    name = reservation.customer_name
    return _bilingual(
        to,
        (f"DaTeNO: Đã nhận yêu cầu đặt bàn #{n}", f"Booking request #{n} received"),
        [
            f"Chào {name},",
            "",
            "DaTeNO đã nhận yêu cầu đặt bàn của quý khách:",
            *_booking_summary(reservation, "vi"),
            "",
            "Nhà hàng sẽ xác nhận sớm và báo lại qua email này.",
            f"Xem hoặc hủy đặt bàn: {_link('/account?tab=bookings')}",
        ],
        [
            f"Hello {name},",
            "",
            "We have received your table booking:",
            *_booking_summary(reservation, "en"),
            "",
            "We will confirm it shortly and let you know by email.",
            f"View or cancel it: {_link('/account?tab=bookings')}",
        ],
    )


def reservation_status_changed(
    reservation: Reservation, to: str, by_customer: bool
) -> Email | None:
    n = reservation.id
    name = reservation.customer_name
    if reservation.status == ReservationStatus.CONFIRMED:
        subject = (f"DaTeNO: Đặt bàn #{n} đã được xác nhận", f"Booking #{n} confirmed")
        vi = ["Bàn của quý khách đã được xác nhận. Hẹn gặp quý khách!"]
        en = ["Your table is confirmed. See you soon!"]
    elif reservation.status == ReservationStatus.CANCELLED:
        subject = (f"DaTeNO: Đặt bàn #{n} đã hủy", f"Booking #{n} cancelled")
        if by_customer:
            vi = ["Quý khách đã hủy đặt bàn sau:"]
            en = ["You cancelled this booking:"]
        else:
            vi = ["Rất tiếc, nhà hàng không thể giữ bàn cho quý khách vào thời gian này:"]
            en = ["Sorry, we cannot hold a table for you at this time:"]
    else:
        return None
    return _bilingual(
        to,
        subject,
        [f"Chào {name},", "", *vi, *_booking_summary(reservation, "vi")],
        [f"Hello {name},", "", *en, *_booking_summary(reservation, "en")],
    )
