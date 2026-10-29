from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DbSession
from app.modules.feedback import service
from app.modules.feedback.schemas import ReviewIn, ReviewOut, TopReviewOut

router = APIRouter(tags=["reviews"])


@router.get("/products/{slug}/reviews", response_model=list[ReviewOut])
def list_reviews(slug: str, db: DbSession):
    return service.list_reviews(db, slug)


@router.post(
    "/products/{slug}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED
)
def add_review(slug: str, data: ReviewIn, db: DbSession, user: CurrentUser):
    return service.add_review(db, user, slug, data)


@router.get("/reviews/top", response_model=list[TopReviewOut])
def top_reviews(db: DbSession, limit: Annotated[int, Query(ge=1, le=20)] = 6):
    return service.top_reviews(db, limit)
