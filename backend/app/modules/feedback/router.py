from typing import Annotated

from fastapi import APIRouter, Query, UploadFile, status

from app.core.deps import CurrentUser, DbSession
from app.core.images import MAX_UPLOAD_BYTES
from app.core.rate_limit import REVIEW_PHOTOS, REVIEWS, rate_limit
from app.modules.feedback import service
from app.modules.feedback.schemas import (
    Eligibility,
    ReviewIn,
    ReviewOut,
    ReviewPage,
    ReviewSort,
    TopReviewOut,
)

router = APIRouter(tags=["reviews"])


@router.get("/products/{slug}/reviews", response_model=ReviewPage)
def list_reviews(
    slug: str,
    db: DbSession,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
    rating: Annotated[int | None, Query(ge=1, le=5)] = None,
    sort: ReviewSort = "newest",
):
    return service.list_reviews(db, slug, page, page_size, rating, sort)


@router.get("/products/{slug}/reviews/eligibility", response_model=Eligibility)
def review_eligibility(slug: str, db: DbSession, user: CurrentUser):
    return service.eligibility(db, user, slug)


@router.post(
    "/products/{slug}/reviews",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(REVIEWS, per="user")],
)
def add_review(slug: str, data: ReviewIn, db: DbSession, user: CurrentUser):
    return service.add_review(db, user, slug, data)


@router.post(
    "/reviews/{review_id}/photos",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(REVIEW_PHOTOS, per="user")],
)
async def add_review_photo(review_id: int, photo: UploadFile, db: DbSession, user: CurrentUser):
    # Read one byte past the limit so oversized files are rejected without loading them fully.
    data = await photo.read(MAX_UPLOAD_BYTES + 1)
    return service.add_photo(db, user, review_id, data)


@router.get("/reviews/top", response_model=list[TopReviewOut])
def top_reviews(db: DbSession, limit: Annotated[int, Query(ge=1, le=20)] = 6):
    return service.top_reviews(db, limit)
