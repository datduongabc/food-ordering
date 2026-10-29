from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.modules.cart import service
from app.modules.cart.schemas import CartItemIn, CartOut, GuestCartIn, QuantityIn

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartOut)
def get_cart(db: DbSession, user: CurrentUser):
    return service.get_cart(db, user)


@router.post("/items", response_model=CartOut)
def add_item(data: CartItemIn, db: DbSession, user: CurrentUser):
    return service.add_item(db, user, data.product_id, data.quantity)


@router.put("/items/{product_id}", response_model=CartOut)
def set_quantity(product_id: int, data: QuantityIn, db: DbSession, user: CurrentUser):
    return service.set_quantity(db, user, product_id, data.quantity)


@router.delete("/items/{product_id}", response_model=CartOut)
def remove_item(product_id: int, db: DbSession, user: CurrentUser):
    return service.remove_item(db, user, product_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(db: DbSession, user: CurrentUser):
    service.clear(db, user)


@router.post("/preview", response_model=CartOut)
def preview_guest_cart(data: GuestCartIn, db: DbSession):
    """Public: prices the guest cart kept in the browser, using current menu prices."""
    return service.preview_guest_cart(db, data.items)


@router.post("/merge", response_model=CartOut)
def merge_guest_cart(data: GuestCartIn, db: DbSession, user: CurrentUser):
    return service.merge_guest_cart(db, user, data.items)
