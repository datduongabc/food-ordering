from collections.abc import Iterable, Sequence
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.modules.cart.models import CartItem
from app.modules.cart.schemas import MAX_QUANTITY, CartItemIn, CartLineOut, CartOut
from app.modules.catalog.models import Product
from app.modules.catalog.schemas import ProductOut
from app.modules.users.models import User


def _build_cart(lines: Iterable[tuple[Product, int]]) -> CartOut:
    items = [
        CartLineOut(
            product=ProductOut.model_validate(product),
            quantity=quantity,
            subtotal=product.price * quantity,
        )
        for product, quantity in lines
    ]
    return CartOut(
        items=items,
        total_count=sum(item.quantity for item in items),
        total_price=sum((item.subtotal for item in items), Decimal("0.00")),
    )


def _active_product(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None or product.deleted_at is not None:
        raise NotFoundError("Dish not found or no longer available.")
    return product


def user_cart_items(db: Session, user: User, *, for_update: bool = False) -> Sequence[CartItem]:
    """Cart lines whose dish is still on the menu; lines for removed dishes are hidden."""
    query = (
        select(CartItem)
        .join(CartItem.product)
        .where(CartItem.user_id == user.id, Product.deleted_at.is_(None))
        .order_by(CartItem.id)
    )
    if for_update:
        query = query.with_for_update(of=CartItem)
    return db.scalars(query).all()


def get_cart(db: Session, user: User) -> CartOut:
    return _build_cart((item.product, item.quantity) for item in user_cart_items(db, user))


def preview_guest_cart(db: Session, lines: list[CartItemIn]) -> CartOut:
    """Prices a browser-held guest cart with current menu prices, dropping unknown dishes."""
    quantities: dict[int, int] = {}
    for line in lines:
        quantities[line.product_id] = min(
            MAX_QUANTITY, quantities.get(line.product_id, 0) + line.quantity
        )
    if not quantities:
        return _build_cart([])

    products = db.scalars(
        select(Product)
        .where(Product.id.in_(quantities), Product.deleted_at.is_(None))
        .order_by(Product.id)
    ).all()
    return _build_cart((product, quantities[product.id]) for product in products)


def _add_quantity(db: Session, user: User, product_id: int, quantity: int) -> None:
    item = db.scalar(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)
    )
    if item is None:
        db.add(CartItem(user_id=user.id, product_id=product_id, quantity=quantity))
    else:
        item.quantity = min(MAX_QUANTITY, item.quantity + quantity)


def add_item(db: Session, user: User, product_id: int, quantity: int) -> CartOut:
    _active_product(db, product_id)
    _add_quantity(db, user, product_id, quantity)
    try:
        db.commit()
    except IntegrityError:
        # A concurrent add (e.g. a double click) inserted the row first; increment it instead.
        db.rollback()
        _add_quantity(db, user, product_id, quantity)
        db.commit()
    return get_cart(db, user)


def set_quantity(db: Session, user: User, product_id: int, quantity: int) -> CartOut:
    item = db.scalar(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)
    )
    if item is None:
        raise NotFoundError("This dish is not in your cart.")
    item.quantity = quantity
    db.commit()
    return get_cart(db, user)


def remove_item(db: Session, user: User, product_id: int) -> CartOut:
    db.execute(
        delete(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)
    )
    db.commit()
    return get_cart(db, user)


def clear(db: Session, user: User) -> None:
    db.execute(delete(CartItem).where(CartItem.user_id == user.id))
    db.commit()


def merge_guest_cart(db: Session, user: User, lines: list[CartItemIn]) -> CartOut:
    """Adds a guest cart into the account cart after sign-in; dishes no longer sold are skipped."""
    preview = preview_guest_cart(db, lines)
    for line in preview.items:
        _add_quantity(db, user, line.product.id, line.quantity)
    db.commit()
    return get_cart(db, user)
