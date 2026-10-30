from typing import Annotated

from fastapi import APIRouter, Query

from app.core.deps import DbSession
from app.modules.catalog import service
from app.modules.catalog.schemas import (
    CategoryOut,
    LocationOut,
    ProductOut,
    ProductPage,
    ProductSort,
)

# Far past the last page of any list; larger numbers would overflow the SQL offset.
MAX_PAGE = 10_000

router = APIRouter(tags=["catalog"])


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: DbSession):
    return service.list_categories(db)


@router.get("/locations", response_model=list[LocationOut])
def list_locations(db: DbSession):
    return service.list_locations(db)


@router.get("/products", response_model=ProductPage)
def list_products(
    db: DbSession,
    page: Annotated[int, Query(ge=1, le=MAX_PAGE)] = 1,
    page_size: Annotated[int, Query(ge=1, le=48)] = 12,
    sort: ProductSort = ProductSort.DEFAULT,
    category: Annotated[str | None, Query(max_length=255, description="Category slug")] = None,
):
    return service.list_products(db, page, page_size, sort, category)


# Declared before /products/{slug} so "featured" and "search" are not captured as slugs.
@router.get("/products/featured", response_model=ProductOut | None)
def featured_product(db: DbSession):
    return service.get_featured_product(db)


@router.get("/products/search", response_model=list[ProductOut])
def search_products(
    db: DbSession,
    q: Annotated[str, Query(min_length=1, max_length=100)],
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
):
    return service.search_products(db, q, limit)


@router.get("/products/{slug}", response_model=ProductOut)
def get_product(slug: str, db: DbSession):
    return service.get_product_by_slug(db, slug)
