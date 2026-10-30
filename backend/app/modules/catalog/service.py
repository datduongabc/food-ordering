import math
from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.core.sql import contains_words
from app.modules.catalog.models import Category, Location, Product
from app.modules.catalog.schemas import ProductOut, ProductPage, ProductSort

# Bayesian average: every dish starts as if it had PRIOR_REVIEWS reviews at PRIOR_RATING, so
# one 5-star review cannot outrank fifty 4.8s. Real reviews pull the score to the true average.
PRIOR_REVIEWS = 5
PRIOR_RATING = 3.5
_score = (
    PRIOR_REVIEWS * PRIOR_RATING + func.coalesce(Product.average_rating, 0) * Product.review_count
) / (PRIOR_REVIEWS + Product.review_count)
# Unrated dishes go last best-first and first worst-first, as if their rating were lowest.
_unrated = Product.review_count == 0

_ORDERINGS = {
    ProductSort.DEFAULT: (Product.id.asc(),),
    ProductSort.PRICE_ASC: (Product.price.asc(), Product.id.asc()),
    ProductSort.PRICE_DESC: (Product.price.desc(), Product.id.asc()),
    ProductSort.RATING_ASC: (_unrated.desc(), _score.asc(), Product.id.asc()),
    ProductSort.RATING_DESC: (_unrated.asc(), _score.desc(), Product.id.asc()),
}


def _active_products() -> Select[tuple[Product]]:
    return select(Product).where(Product.deleted_at.is_(None))


def list_categories(db: Session) -> Sequence[Category]:
    return db.scalars(
        select(Category).where(Category.deleted_at.is_(None)).order_by(Category.id)
    ).all()


def list_locations(db: Session) -> Sequence[Location]:
    return db.scalars(select(Location).order_by(Location.id)).all()


def list_products(
    db: Session, page: int, page_size: int, sort: ProductSort, category: str | None
) -> ProductPage:
    query = _active_products()
    if category is not None:
        query = query.join(Product.category).where(Category.slug == category)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    products = db.scalars(
        query.order_by(*_ORDERINGS[sort]).limit(page_size).offset((page - 1) * page_size)
    ).all()
    return ProductPage(
        items=[ProductOut.model_validate(p) for p in products],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=max(1, math.ceil(total / page_size)),
    )


def get_featured_product(db: Session) -> Product | None:
    return db.scalar(_active_products().order_by(*_ORDERINGS[ProductSort.RATING_DESC]).limit(1))


def search_products(db: Session, term: str, limit: int) -> Sequence[Product]:
    return db.scalars(
        _active_products()
        .where(contains_words(Product.search_text, term))
        .order_by(*_ORDERINGS[ProductSort.RATING_DESC])
        .limit(limit)
    ).all()


def get_product_by_slug(db: Session, slug: str) -> Product:
    product = db.scalar(_active_products().where(Product.slug == slug))
    if product is None:
        raise NotFoundError("Dish not found.", code="dish_not_found")
    return product
