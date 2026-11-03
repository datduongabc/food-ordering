from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.core.cache import CacheDep
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
def list_categories(db: DbSession, cache: CacheDep):
    cached = cache.get("categories")
    if cached is not None:
        return JSONResponse(cached)
    data = [
        CategoryOut.model_validate(c).model_dump(mode="json") for c in service.list_categories(db)
    ]
    cache.set("categories", data)
    return JSONResponse(data)


@router.get("/locations", response_model=list[LocationOut])
def list_locations(db: DbSession, cache: CacheDep):
    cached = cache.get("locations")
    if cached is not None:
        return JSONResponse(cached)
    data = [
        LocationOut.model_validate(loc).model_dump(mode="json")
        for loc in service.list_locations(db)
    ]
    cache.set("locations", data)
    return JSONResponse(data)


@router.get("/products", response_model=ProductPage)
def list_products(
    db: DbSession,
    cache: CacheDep,
    page: Annotated[int, Query(ge=1, le=MAX_PAGE)] = 1,
    page_size: Annotated[int, Query(ge=1, le=48)] = 12,
    sort: ProductSort = ProductSort.DEFAULT,
    category: Annotated[str | None, Query(max_length=255, description="Category slug")] = None,
):
    key = f"products:{page}:{page_size}:{sort.value}:{category or ''}"
    cached = cache.get(key)
    if cached is not None:
        return JSONResponse(cached)
    data = service.list_products(db, page, page_size, sort, category).model_dump(mode="json")
    cache.set(key, data)
    return JSONResponse(data)


# Declared before /products/{slug} so "featured" and "search" are not captured as slugs.
@router.get("/products/featured", response_model=ProductOut | None)
def featured_product(db: DbSession, cache: CacheDep):
    cached = cache.get("featured")
    if cached is not None:
        return JSONResponse(cached["item"])
    product = service.get_featured_product(db)
    item = ProductOut.model_validate(product).model_dump(mode="json") if product else None
    cache.set("featured", {"item": item})
    return JSONResponse(item)


@router.get("/products/search", response_model=list[ProductOut])
def search_products(
    db: DbSession,
    cache: CacheDep,
    q: Annotated[str, Query(min_length=1, max_length=100)],
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
):
    key = f"search:{q.strip().lower()}:{limit}"
    cached = cache.get(key)
    if cached is not None:
        return JSONResponse(cached)
    data = [
        ProductOut.model_validate(p).model_dump(mode="json")
        for p in service.search_products(db, q, limit)
    ]
    cache.set(key, data)
    return JSONResponse(data)


@router.get("/products/{slug}", response_model=ProductOut)
def get_product(slug: str, db: DbSession, cache: CacheDep):
    key = f"product:{slug}"
    cached = cache.get(key)
    if cached is not None:
        return JSONResponse(cached)
    product = service.get_product_by_slug(db, slug)
    data = ProductOut.model_validate(product).model_dump(mode="json")
    cache.set(key, data)
    return JSONResponse(data)
