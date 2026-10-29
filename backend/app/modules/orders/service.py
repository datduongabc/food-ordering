from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.modules.cart.models import CartItem
from app.modules.cart.service import user_cart_items
from app.modules.orders.models import Order, OrderItem, OrderStatus, PaymentMethod
from app.modules.users.models import User


def place_order(db: Session, user: User, payment_method: PaymentMethod) -> Order:
    # Locking the cart rows makes a double-submitted checkout wait, then find the cart empty,
    # instead of creating two orders from the same cart.
    cart = user_cart_items(db, user, for_update=True)
    if not cart:
        raise BadRequestError("Your cart is empty. Add some dishes before placing an order.")

    order = Order(
        user_id=user.id,
        payment_method=payment_method,
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
    if order.status != OrderStatus.PENDING:
        raise ConflictError("Only pending orders can be cancelled.")
    order.status = OrderStatus.CANCELLED
    db.commit()
    return order
