from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError
from app.modules.catalog.models import Product
from app.modules.catalog.service import get_product_by_slug
from app.modules.feedback.models import Review
from app.modules.feedback.schemas import ReviewIn
from app.modules.users.models import User

ALREADY_REVIEWED = "You have already reviewed this dish."


def list_reviews(db: Session, slug: str) -> Sequence[Review]:
    product = get_product_by_slug(db, slug)
    return db.scalars(
        select(Review)
        .where(Review.product_id == product.id)
        .order_by(Review.created_at.desc(), Review.id.desc())
    ).all()


def add_review(db: Session, user: User, slug: str, data: ReviewIn) -> Review:
    product = get_product_by_slug(db, slug)
    # Row lock serialises concurrent reviews of one dish, so the recomputed average
    # always includes every committed review (no-op on SQLite, which locks the whole db).
    db.execute(select(Product.id).where(Product.id == product.id).with_for_update())

    if db.scalar(
        select(Review.id).where(Review.user_id == user.id, Review.product_id == product.id)
    ):
        raise ConflictError(ALREADY_REVIEWED, code="already_reviewed")

    review = Review(
        user_id=user.id, product_id=product.id, rating=data.rating, comment=data.comment
    )
    db.add(review)
    try:
        db.flush()
    except IntegrityError as exc:  # lost a race with a duplicate submit from the same user
        db.rollback()
        raise ConflictError(ALREADY_REVIEWED, code="already_reviewed") from exc

    product.average_rating = db.scalar(
        select(func.round(func.avg(Review.rating), 2)).where(Review.product_id == product.id)
    )
    db.commit()
    db.refresh(review)
    return review


def top_reviews(db: Session, limit: int) -> Sequence[Review]:
    return db.scalars(
        select(Review)
        .join(Review.product)
        .where(Product.deleted_at.is_(None))
        .order_by(Review.rating.desc(), Review.created_at.desc(), Review.id.desc())
        .limit(limit)
    ).all()
