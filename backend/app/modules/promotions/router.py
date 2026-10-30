from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.core.errors import BadRequestError
from app.core.rate_limit import PROMO_CHECKS, rate_limit
from app.modules.cart.service import user_cart_items
from app.modules.promotions import service
from app.modules.promotions.schemas import PromoCheckIn, PromoQuoteOut

router = APIRouter(tags=["promotions"])


@router.post(
    "/promo-codes/check",
    response_model=PromoQuoteOut,
    # Tight enough that guessing codes one request at a time is not worth it.
    dependencies=[rate_limit(PROMO_CHECKS, per="user")],
)
def check_promo_code(data: PromoCheckIn, db: DbSession, user: CurrentUser):
    """Prices the signed-in customer's cart with a code before checkout."""
    cart = user_cart_items(db, user)
    if not cart:
        raise BadRequestError(
            "Your cart is empty. Add some dishes before placing an order.", code="cart_empty"
        )
    subtotal = sum(line.product.price * line.quantity for line in cart)
    quote = service.quote(db, user, data.code, subtotal)
    return PromoQuoteOut(
        code=quote.promo.code,
        kind=quote.promo.kind,
        value=quote.promo.value,
        subtotal=quote.subtotal,
        discount=quote.discount,
        total=quote.total,
    )
