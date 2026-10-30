import math
import secrets
from collections.abc import Sequence
from datetime import timedelta

from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import images
from app.core.config import get_settings
from app.core.db import utcnow
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.modules.catalog.models import Product
from app.modules.catalog.service import get_product_by_slug
from app.modules.feedback.models import Review, ReviewPhoto
from app.modules.feedback.schemas import (
    REVIEW_MEDIA,
    Eligibility,
    RatingBucket,
    RatingSummary,
    ReviewIn,
    ReviewOut,
    ReviewPage,
    ReviewSort,
)
from app.modules.orders.models import Order, OrderItem, OrderStatus
from app.modules.users.models import User

ALREADY_REVIEWED = "You have already reviewed this dish."
MAX_PHOTOS = 3
# Photos follow the review they belong to; later on, a review stays as it was posted.
PHOTO_WINDOW = timedelta(hours=1)

_ORDERINGS = {
    "newest": (Review.created_at.desc(), Review.id.desc()),
    "highest": (Review.rating.desc(), Review.created_at.desc(), Review.id.desc()),
    "lowest": (Review.rating.asc(), Review.created_at.desc(), Review.id.desc()),
}


def _visible():
    return Review.hidden_at.is_(None)


def purchased(db: Session, user_id: int, product_id: int) -> bool:
    """Whether the customer has a delivered order with this dish in it."""
    return bool(
        db.scalar(
            select(
                exists()
                .where(OrderItem.order_id == Order.id)
                .where(
                    Order.user_id == user_id,
                    Order.status == OrderStatus.COMPLETED,
                    OrderItem.product_id == product_id,
                )
            )
        )
    )


def refresh_rating(db: Session, product_id: int) -> None:
    """Recomputes a dish's average and count from its visible reviews."""
    count, average = db.execute(
        select(func.count(Review.id), func.round(func.avg(Review.rating), 2)).where(
            Review.product_id == product_id, _visible()
        )
    ).one()
    product = db.get(Product, product_id)
    assert product is not None
    product.review_count = count
    product.average_rating = average


def summary(db: Session, product: Product) -> RatingSummary:
    rows = dict(
        db.execute(
            select(Review.rating, func.count(Review.id))
            .where(Review.product_id == product.id, _visible())
            .group_by(Review.rating)
        ).all()
    )
    return RatingSummary(
        average=product.average_rating,
        count=product.review_count,
        distribution=[RatingBucket(stars=s, count=rows.get(s, 0)) for s in range(5, 0, -1)],
    )


def list_reviews(
    db: Session, slug: str, page: int, page_size: int, rating: int | None, sort: ReviewSort
) -> ReviewPage:
    product = get_product_by_slug(db, slug)
    query = select(Review).where(Review.product_id == product.id, _visible())
    if rating is not None:
        query = query.where(Review.rating == rating)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    reviews = db.scalars(
        query.order_by(*_ORDERINGS[sort]).limit(page_size).offset((page - 1) * page_size)
    ).all()
    return ReviewPage(
        items=[ReviewOut.model_validate(r) for r in reviews],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=max(1, math.ceil(total / page_size)),
        summary=summary(db, product),
    )


def eligibility(db: Session, user: User, slug: str) -> Eligibility:
    product = get_product_by_slug(db, slug)
    if db.scalar(
        select(Review.id).where(Review.user_id == user.id, Review.product_id == product.id)
    ):
        return Eligibility(can_review=False, reason="already_reviewed")
    if not purchased(db, user.id, product.id):
        return Eligibility(can_review=False, reason="not_purchased")
    return Eligibility(can_review=True)


def add_review(db: Session, user: User, slug: str, data: ReviewIn) -> Review:
    product = get_product_by_slug(db, slug)
    # Row lock serialises concurrent reviews of one dish, so the recomputed average
    # always includes every committed review (no-op on SQLite, which locks the whole db).
    db.execute(select(Product.id).where(Product.id == product.id).with_for_update())

    if db.scalar(
        select(Review.id).where(Review.user_id == user.id, Review.product_id == product.id)
    ):
        raise ConflictError(ALREADY_REVIEWED, code="already_reviewed")
    # Only someone who has eaten the dish may rate it, which keeps the average honest.
    if not purchased(db, user.id, product.id):
        raise ForbiddenError(
            "Only customers with a delivered order of this dish can review it.",
            code="review_needs_purchase",
        )

    review = Review(
        user_id=user.id,
        product_id=product.id,
        rating=data.rating,
        comment=data.comment,
        verified_purchase=True,
    )
    db.add(review)
    try:
        db.flush()
    except IntegrityError as exc:  # lost a race with a duplicate submit from the same user
        db.rollback()
        raise ConflictError(ALREADY_REVIEWED, code="already_reviewed") from exc

    refresh_rating(db, product.id)
    db.commit()
    db.refresh(review)
    return review


def add_photo(db: Session, user: User, review_id: int, data: bytes) -> Review:
    # Locked so two uploads at once cannot both slip under the photo limit.
    db.execute(select(Review.id).where(Review.id == review_id).with_for_update())
    review = db.get(Review, review_id)
    # Someone else's review looks the same as a missing one.
    if review is None or review.user_id != user.id or review.hidden_at is not None:
        raise NotFoundError("Review not found.", code="review_not_found")
    if utcnow() - review.created_at > PHOTO_WINDOW:
        raise ForbiddenError(
            "Photos can only be added within an hour of posting.", code="review_photos_closed"
        )
    if len(review.photos) >= MAX_PHOTOS:
        raise ConflictError(
            f"A review can have at most {MAX_PHOTOS} photos.",
            code="review_photos_full",
            params={"max": MAX_PHOTOS},
        )

    photo, thumb = images.accept_upload(data)
    reviews_dir = get_settings().media_dir / REVIEW_MEDIA
    # The review id keeps one customer's photos together; the random part makes names unguessable.
    relative = f"{review.id}-{secrets.token_hex(8)}.webp"
    for path, content in ((relative, photo), (images.thumbnail_path(relative), thumb)):
        (reviews_dir / path).parent.mkdir(parents=True, exist_ok=True)
        (reviews_dir / path).write_bytes(content)

    review.photos.append(ReviewPhoto(path=relative))
    db.commit()
    db.refresh(review)
    return review


def top_reviews(db: Session, limit: int) -> Sequence[Review]:
    return db.scalars(
        select(Review)
        .join(Review.product)
        .where(Product.deleted_at.is_(None), _visible())
        .order_by(Review.rating.desc(), Review.created_at.desc(), Review.id.desc())
        .limit(limit)
    ).all()
