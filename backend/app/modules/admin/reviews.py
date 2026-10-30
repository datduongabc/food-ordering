from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import utcnow
from app.core.errors import NotFoundError
from app.modules.admin import audit
from app.modules.admin.pagination import paginate
from app.modules.admin.schemas import Page, ReviewVisibility
from app.modules.catalog.models import Product
from app.modules.feedback.models import Review
from app.modules.feedback.service import refresh_rating
from app.modules.users.models import User


def list_reviews(
    db: Session,
    visibility: ReviewVisibility | None,
    rating: int | None,
    product: str | None,
    page: int,
    page_size: int,
) -> Page[Review]:
    query = select(Review).order_by(Review.created_at.desc(), Review.id.desc())
    if visibility == "visible":
        query = query.where(Review.hidden_at.is_(None))
    elif visibility == "hidden":
        query = query.where(Review.hidden_at.is_not(None))
    if rating is not None:
        query = query.where(Review.rating == rating)
    if product:
        query = query.join(Review.product).where(Product.slug == product)
    return paginate(db, query, page, page_size)


def _get(db: Session, review_id: int) -> Review:
    review = db.get(Review, review_id)
    if review is None:
        raise NotFoundError("Review not found.", code="review_not_found")
    return review


def _label(review: Review) -> str:
    return f"{review.user.name}: {review.product.name['vi']} ({review.rating}★)"


def _lock_product(db: Session, review: Review) -> None:
    # The same lock new reviews take, so the recomputed average cannot miss one.
    db.execute(select(Product.id).where(Product.id == review.product_id).with_for_update())


def hide_review(db: Session, admin: User, review_id: int) -> Review:
    review = _get(db, review_id)
    if review.hidden_at is None:
        _lock_product(db, review)
        review.hidden_at = utcnow()
        db.flush()
        refresh_rating(db, review.product_id)
        audit.record(db, admin, "review.hide", "review", review.id, _label(review))
        db.commit()
    return review


def restore_review(db: Session, admin: User, review_id: int) -> Review:
    review = _get(db, review_id)
    if review.hidden_at is not None:
        _lock_product(db, review)
        review.hidden_at = None
        db.flush()
        refresh_rating(db, review.product_id)
        audit.record(db, admin, "review.restore", "review", review.id, _label(review))
        db.commit()
    return review


def reply_to_review(db: Session, admin: User, review_id: int, reply: str) -> Review:
    review = _get(db, review_id)
    new = reply or None
    if new != review.reply:
        audit.record(
            db,
            admin,
            "review.reply",
            "review",
            review.id,
            _label(review),
            {"reply": [review.reply, new]},
        )
        review.reply = new
        review.replied_at = utcnow() if new else None
        db.commit()
    return review
