from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, StringConstraints, computed_field

from app.core.config import get_settings
from app.core.images import thumbnail_path
from app.core.localized import LocalizedText

REVIEW_MEDIA = "reviews"


class ReviewIn(BaseModel):
    rating: Annotated[int, Field(ge=1, le=5)]
    comment: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class ReviewPhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    path: str = Field(exclude=True)

    @computed_field
    @property
    def url(self) -> str:
        return f"{get_settings().media_url}/{REVIEW_MEDIA}/{self.path}"

    @computed_field
    @property
    def thumbnail_url(self) -> str:
        return f"{get_settings().media_url}/{REVIEW_MEDIA}/{thumbnail_path(self.path)}"


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rating: int
    comment: str
    created_at: datetime
    # Only the display name is public; the reviewer's email and phone never leave the API.
    user_name: str = Field(validation_alias=AliasPath("user", "name"))
    verified_purchase: bool
    reply: str | None
    replied_at: datetime | None
    photos: list[ReviewPhotoOut]


class TopReviewOut(ReviewOut):
    product_name: LocalizedText = Field(validation_alias=AliasPath("product", "name"))
    product_slug: str = Field(validation_alias=AliasPath("product", "slug"))


ReviewSort = Literal["newest", "highest", "lowest"]


class RatingBucket(BaseModel):
    stars: int
    count: int


class RatingSummary(BaseModel):
    average: Decimal | None
    count: int
    # Five buckets, 5 stars first, each with how many visible reviews gave that many.
    distribution: list[RatingBucket]


class ReviewPage(BaseModel):
    items: list[ReviewOut]
    page: int
    page_size: int
    total: int
    total_pages: int
    summary: RatingSummary


class Eligibility(BaseModel):
    can_review: bool
    # Why not: no delivered order of the dish yet, or a review already written.
    reason: Literal["not_purchased", "already_reviewed"] | None = None
