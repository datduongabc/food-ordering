from typing import Annotated

from pydantic import BaseModel, Field

from app.modules.catalog.schemas import ProductOut

MAX_QUANTITY = 99

Quantity = Annotated[int, Field(ge=1, le=MAX_QUANTITY)]


class CartItemIn(BaseModel):
    product_id: int
    quantity: Quantity = 1


class QuantityIn(BaseModel):
    quantity: Quantity


class GuestCartIn(BaseModel):
    # Bounded so a crafted request cannot make the server price thousands of lines.
    items: Annotated[list[CartItemIn], Field(max_length=100)]


class CartLineOut(BaseModel):
    product: ProductOut
    quantity: int
    subtotal: int


class CartOut(BaseModel):
    items: list[CartLineOut]
    total_count: int
    total_price: int
