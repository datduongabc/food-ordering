from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.modules.promotions.models import DiscountKind

# Loose on purpose: whatever is typed is looked up, and an unknown code gets a clear answer.
CodeIn = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)]


class PromoCheckIn(BaseModel):
    code: CodeIn


class PromoQuoteOut(BaseModel):
    code: str
    kind: DiscountKind
    value: int
    subtotal: int
    discount: int
    total: int
