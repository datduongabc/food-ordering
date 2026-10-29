from datetime import datetime
from typing import Annotated

from pydantic import AliasPath, BaseModel, ConfigDict, Field, StringConstraints

from app.core.localized import LocalizedText


class ReviewIn(BaseModel):
    rating: Annotated[int, Field(ge=1, le=5)]
    comment: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rating: int
    comment: str
    created_at: datetime
    # Only the display name is public; the reviewer's email and phone never leave the API.
    user_name: str = Field(validation_alias=AliasPath("user", "name"))


class TopReviewOut(ReviewOut):
    product_name: LocalizedText = Field(validation_alias=AliasPath("product", "name"))
    product_slug: str = Field(validation_alias=AliasPath("product", "slug"))
