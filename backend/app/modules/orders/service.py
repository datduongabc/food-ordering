from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.modules.cart.models import CartItem
from app.modules.cart.service import user_cart_items
from app.modules.catalog.models import Location
from app.modules.orders.models import (
    ORDER_TRANSITIONS,
    Order,
    OrderEvent,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.modules.orders.schemas import CheckoutIn
from app.modules.users.models import User


def transition(order: Order, to: OrderStatus, actor: User | None, note: str = "") -> None:
    """The only way an order changes status, so every change is validated and recorded."""
    if to not in ORDER_TRANSITIONS[order.status]:
        raise ConflictError(
            f"Order #{order.id} is {order.status.lower()} and cannot become {to.lower()}."
        )

    if to == OrderStatus.CANCELLED and order.payment_status == PaymentStatus.PAID:
        # Money already taken must go back; staff refund MoMo payments from the MoMo portal.
        order.payment_status = PaymentStatus.REFUNDED
        note = note or "Payment to be refunded."
    if to == OrderStatus.COMPLETED and order.payment_method == PaymentMethod.COD:
        order.payment_status = PaymentStatus.PAID  # cash collected on delivery

    order.events.append(
        OrderEvent(
            from_status=order.status,
            to_status=to,
            actor_id=actor.id if actor else None,
            note=note,
        )
    )
    order.status = to


def place_order(db: Session, user: User, data: CheckoutIn) -> Order:
    # Locking the cart rows makes a double-submitted checkout wait, then find the cart empty,
    # instead of creating two orders from the same cart.
    cart = user_cart_items(db, user, for_update=True)
    if not cart:
        raise BadRequestError("Your cart is empty. Add some dishes before placing an order.")

    location = db.get(Location, data.location_id)
    if location is None:
        raise BadRequestError("Please choose one of our branches.")
    unavailable = [line.product.name for line in cart if location not in line.product.locations]
    if unavailable:
        raise BadRequestError(
            f"Not available at {location.name}: {', '.join(unavailable)}. "
            "Remove them or choose another branch."
        )

    order = Order(
        user_id=user.id,
        payment_method=data.payment_method,
        location=location,
        delivery_name=data.delivery_name,
        delivery_phone=data.delivery_phone,
        delivery_address=data.delivery_address,
        delivery_note=data.delivery_note,
        events=[OrderEvent(from_status=None, to_status=OrderStatus.PENDING, actor_id=user.id)],
        # Prices are snapshotted so later menu price changes do not alter past orders.
        items=[
            OrderItem(
                product=line.product,
                price_at_purchase=line.product.price,
                quantity=line.quantity,
            )
            for line in cart
        ],
    )
    order.total_price = sum(
        (item.price_at_purchase * item.quantity for item in order.items), Decimal("0.00")
    )
    db.add(order)
    db.execute(delete(CartItem).where(CartItem.user_id == user.id))
    db.commit()
    db.refresh(order)
    return order


def list_orders(db: Session, user: User) -> Sequence[Order]:
    return db.scalars(
        select(Order)
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc(), Order.id.desc())
    ).all()


def get_order(db: Session, user: User, order_id: int, *, for_update: bool = False) -> Order:
    query = select(Order).where(Order.id == order_id, Order.user_id == user.id)
    if for_update:
        query = query.with_for_update(of=Order)
    order = db.scalar(query)
    if order is None:
        # Same response for someone else's order, so order ids cannot be probed.
        raise NotFoundError("Order not found.")
    return order


def cancel_order(db: Session, user: User, order_id: int) -> Order:
    order = get_order(db, user, order_id, for_update=True)
    # Customers may only back out before the kitchen confirms; staff can cancel later.
    if order.status != OrderStatus.PENDING:
        raise ConflictError("Only pending orders can be cancelled. Please call the restaurant.")
    transition(order, OrderStatus.CANCELLED, user, "Cancelled by customer.")
    db.commit()
    return order
