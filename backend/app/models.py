"""Imports every model so Base.metadata is complete for Alembic and test schema creation."""

from app.modules.admin.models import AuditLog
from app.modules.auth.models import OtpCode, UserSession
from app.modules.cart.models import CartItem
from app.modules.catalog.models import Category, Location, Product, product_availabilities
from app.modules.feedback.models import Review, ReviewPhoto
from app.modules.orders.models import Order, OrderEvent, OrderItem
from app.modules.promotions.models import PromoCode
from app.modules.reservations.models import Reservation
from app.modules.users.models import User

__all__ = [
    "AuditLog",
    "CartItem",
    "Category",
    "Location",
    "OtpCode",
    "Order",
    "OrderEvent",
    "OrderItem",
    "Product",
    "PromoCode",
    "Reservation",
    "Review",
    "ReviewPhoto",
    "User",
    "UserSession",
    "product_availabilities",
]
