import re
import secrets
import unicodedata
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.modules.admin.schemas import ProductCreate, ProductUpdate
from app.modules.catalog.models import Category, Location, Product

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
        raise NotFoundError("Dish not found.")
    return product


def _category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None or category.deleted_at is not None:
        raise BadRequestError("Unknown category.")
    return category


def _locations(db: Session, location_ids: list[int]) -> list[Location]:
    ids = set(location_ids)
    locations = db.scalars(select(Location).where(Location.id.in_(ids))).all()
    if len(locations) != len(ids):
        raise BadRequestError("Unknown branch selected.")
    return list(locations)


def _commit_unique_slug(db: Session, slug: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(f'Another dish already uses the URL "{slug}".') from exc


def create_product(db: Session, data: ProductCreate) -> Product:
    slug = data.slug or slugify(data.name)
    if not slug:
        raise BadRequestError("Please provide a URL slug for this dish name.")
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
    _commit_unique_slug(db, slug)
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    changes = data.model_dump(exclude_unset=True)
    if "category_id" in changes:
        product.category = _category(db, changes.pop("category_id"))
    if "location_ids" in changes:
        product.locations = _locations(db, changes.pop("location_ids"))
    for field, value in changes.items():
        setattr(product, field, value)
    _commit_unique_slug(db, product.slug)
    db.refresh(product)
    return product


def replace_image(db: Session, product_id: int, data: bytes) -> Product:
    product = get_product(db, product_id)
    if len(data) > MAX_IMAGE_BYTES:
        raise BadRequestError("Images must be 5 MB or smaller.")
    extension = image_extension(data)
    if extension is None:
        raise BadRequestError("Only JPEG, PNG and WebP images are allowed.")

    products_dir = get_settings().media_dir / "products"
    (products_dir / UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    # A fresh name per upload: never overwrites another dish's photo and busts browser caches.
    relative = f"{UPLOAD_DIR}/{product.slug}-{secrets.token_hex(4)}.{extension}"
    (products_dir / relative).write_bytes(data)

    previous = product.image_url
    product.image_url = relative
    db.commit()
    # Only earlier uploads are removed; seeded photos may be shared and are part of the repo.
    if previous.startswith(f"{UPLOAD_DIR}/"):
        (products_dir / previous).unlink(missing_ok=True)
    db.refresh(product)
    return product


def hide_product(db: Session, product_id: int) -> Product:
    product = get_product(db, product_id)
    if product.deleted_at is None:
        product.deleted_at = utcnow()
        db.commit()
    return product


def restore_product(db: Session, product_id: int) -> Product:
    product = get_product(db, product_id)
    product.deleted_at = None
    db.commit()
    return product
