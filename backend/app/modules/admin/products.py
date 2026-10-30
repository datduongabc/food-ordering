import re
import secrets
import unicodedata
from collections.abc import Callable, Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import images
from app.core.config import get_settings
from app.core.db import utcnow
from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.modules.admin import audit
from app.modules.admin.schemas import ProductCreate, ProductUpdate
from app.modules.catalog.models import Category, Location, Product
from app.modules.users.models import User

MAX_IMAGE_BYTES = 5 * 1024 * 1024
UPLOAD_DIR = "uploads"


def slugify(text: str) -> str:
    # Vietnamese dish names ("Phở bò") become ASCII slugs ("pho-bo"); đ has no decomposition.
    ascii_text = (
        unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
        .encode("ascii", "ignore")
        .decode()
    )
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def image_extension(data: bytes) -> str | None:
    """Identifies the format from the file's magic bytes; the client's filename is not trusted."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def list_products(db: Session) -> Sequence[Product]:
    return db.scalars(select(Product).order_by(Product.id)).all()


def get_product(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise NotFoundError("Dish not found.", code="dish_not_found")
    return product


def _category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None or category.deleted_at is not None:
        raise BadRequestError("Unknown category.", code="unknown_category")
    return category


def _locations(db: Session, location_ids: list[int]) -> list[Location]:
    ids = set(location_ids)
    locations = db.scalars(select(Location).where(Location.id.in_(ids))).all()
    if len(locations) != len(ids):
        raise BadRequestError("Unknown branch selected.", code="unknown_branch")
    return list(locations)


def _snapshot(product: Product) -> dict[str, Any]:
    """The fields staff can edit, as the audit log records them."""
    return {
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "price": product.price,
        "category_id": product.category.id,
        "location_ids": sorted(location.id for location in product.locations),
    }


def _commit_unique_slug(
    db: Session, slug: str, before_commit: Callable[[], None] = lambda: None
) -> None:
    try:
        # Flushing first gives a new dish its id for the audit entry, inside the same transaction.
        db.flush()
        before_commit()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            f'Another dish already uses the URL "{slug}".', code="slug_taken", params={"slug": slug}
        ) from exc


def create_product(db: Session, admin: User, data: ProductCreate) -> Product:
    slug = data.slug or slugify(data.name.en)
    if not slug:
        raise BadRequestError("Please provide a URL slug for this dish name.", code="slug_required")
    category = _category(db, data.category_id)
    product = Product(
        name=data.name,
        slug=slug,
        description=data.description,
        price=data.price,
        category=category,
        locations=_locations(db, data.location_ids),
        # Placeholder until a photo is uploaded, so the menu never shows a broken image.
        image_url="placeholder.webp",
    )
    db.add(product)
    _commit_unique_slug(
        db,
        slug,
        lambda: audit.record(
            db,
            admin,
            "product.create",
            "product",
            product.id,
            product.name["vi"],
            audit.created(_snapshot(product)),
        ),
    )
    db.refresh(product)
    return product


def update_product(db: Session, admin: User, product_id: int, data: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    before = _snapshot(product)
    changes = data.model_dump(exclude_unset=True)
    if "category_id" in changes:
        product.category = _category(db, changes.pop("category_id"))
    if "location_ids" in changes:
        product.locations = _locations(db, changes.pop("location_ids"))
    for field, value in changes.items():
        setattr(product, field, value)

    def log_changes() -> None:
        if changed := audit.diff(before, _snapshot(product)):
            audit.record(
                db, admin, "product.update", "product", product.id, product.name["vi"], changed
            )

    _commit_unique_slug(db, product.slug, log_changes)
    db.refresh(product)
    return product


def replace_image(db: Session, admin: User, product_id: int, data: bytes) -> Product:
    product = get_product(db, product_id)
    if len(data) > MAX_IMAGE_BYTES:
        raise BadRequestError(
            "Images must be 5 MB or smaller.", code="image_too_large", params={"max_mb": 5}
        )
    # The magic bytes keep Pillow to the three formats a photo arrives in.
    if image_extension(data) is None:
        raise BadRequestError(
            "Only JPEG, PNG and WebP images are allowed.", code="image_type_not_allowed"
        )

    try:
        # Re-encoding also drops anything hidden in the file and the photo's EXIF location.
        photo, thumb = images.process_upload(data)
    except images.InvalidImage as exc:
        raise BadRequestError(
            "Only JPEG, PNG and WebP images are allowed.", code="image_type_not_allowed"
        ) from exc

    products_dir = get_settings().media_dir / "products"
    # A fresh name per upload: never overwrites another dish's photo and busts browser caches.
    relative = f"{UPLOAD_DIR}/{product.slug}-{secrets.token_hex(4)}.webp"
    for path, content in ((relative, photo), (images.thumbnail_path(relative), thumb)):
        (products_dir / path).parent.mkdir(parents=True, exist_ok=True)
        (products_dir / path).write_bytes(content)

    previous = product.image_url
    product.image_url = relative
    audit.record(
        db,
        admin,
        "product.image",
        "product",
        product.id,
        product.name["vi"],
        {"image_url": [previous, relative]},
    )
    db.commit()
    # Only earlier uploads are removed; seeded photos may be shared and are part of the repo.
    if previous.startswith(f"{UPLOAD_DIR}/"):
        (products_dir / previous).unlink(missing_ok=True)
        (products_dir / images.thumbnail_path(previous)).unlink(missing_ok=True)
    db.refresh(product)
    return product


def hide_product(db: Session, admin: User, product_id: int) -> Product:
    product = get_product(db, product_id)
    if product.deleted_at is None:
        product.deleted_at = utcnow()
        audit.record(db, admin, "product.hide", "product", product.id, product.name["vi"])
        db.commit()
    return product


def restore_product(db: Session, admin: User, product_id: int) -> Product:
    product = get_product(db, product_id)
    if product.deleted_at is not None:
        product.deleted_at = None
        audit.record(db, admin, "product.restore", "product", product.id, product.name["vi"])
        db.commit()
    return product
