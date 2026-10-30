"""Dish photos: uploads are decoded and re-encoded as WebP, and every photo gets a thumbnail.

A thumbnail lives at `thumbs/<photo path>.webp` beside the photos, so its URL follows from
the photo's without a database column.
"""

import io
import warnings
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.errors import BadRequestError

# Big enough for a 4:3 menu card or the dish page on a large screen.
FULL_SIZE = 1200
# Menu cards are 250-400 CSS pixels wide, cart and order lines far smaller. 640 stays sharp on
# a 2x screen at card size, at about a fifth of the full photo's bytes; a srcset handing dense
# phone screens the full photo would undo most of the saving.
THUMB_SIZE = 640
QUALITY = 80
THUMBS_DIR = "thumbs"
# A 5 MB upload can still decode to gigabytes of pixels; refuse anything past ~40 megapixels.
MAX_PIXELS = 40_000_000
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class InvalidImage(ValueError):
    """The bytes are not a photo Pillow can safely decode."""


PHOTO_SUFFIXES = (".webp", ".jpg", ".png")


def thumbnail_path(image_path: str) -> str:
    """Always WebP, even for a JPEG or PNG uploaded before uploads were converted."""
    return f"{THUMBS_DIR}/{image_path.rsplit('.', 1)[0]}.webp"


def _encode(image: Image.Image, size: int) -> bytes:
    copy = image.copy()
    copy.thumbnail((size, size), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    # No exif= argument: the location and camera details a phone embeds are not carried over.
    copy.save(out, "WEBP", quality=QUALITY, method=6)
    return out.getvalue()


def _open(data: bytes) -> Image.Image:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(io.BytesIO(data))
            if image.width * image.height > MAX_PIXELS:
                raise InvalidImage("too many pixels")
            image.load()  # first frame only, for animated files
    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
    ) as exc:
        raise InvalidImage(str(exc)) from exc
    # Phones store portrait shots sideways with a rotation flag; apply it before it is lost.
    image = ImageOps.exif_transpose(image)
    return image.convert("RGBA" if "A" in image.getbands() else "RGB")


def process_upload(data: bytes) -> tuple[bytes, bytes]:
    """The photo and its thumbnail as WebP, whatever format and size came in."""
    image = _open(data)
    return _encode(image, FULL_SIZE), _encode(image, THUMB_SIZE)


def image_extension(data: bytes) -> str | None:
    """Identifies the format from the file's magic bytes; the client's filename is not trusted."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def accept_upload(data: bytes) -> tuple[bytes, bytes]:
    """Checks an uploaded photo and re-encodes it, which also drops anything hidden in the
    file and the photo's EXIF location. Raises the errors the SPA explains to the user."""
    if not data:
        raise BadRequestError("The uploaded file is empty.", code="empty_upload")
    if len(data) > MAX_UPLOAD_BYTES:
        raise BadRequestError(
            "Images must be 5 MB or smaller.", code="image_too_large", params={"max_mb": 5}
        )
    # The magic bytes keep Pillow to the three formats a photo arrives in.
    if image_extension(data) is None:
        raise BadRequestError(
            "Only JPEG, PNG and WebP images are allowed.", code="image_type_not_allowed"
        )
    try:
        return process_upload(data)
    except InvalidImage as exc:
        raise BadRequestError(
            "Only JPEG, PNG and WebP images are allowed.", code="image_type_not_allowed"
        ) from exc


def ensure_thumbnails(products_dir: Path) -> int:
    """Makes the missing thumbnails for every photo under `products_dir`; returns how many."""
    made = 0
    for photo in sorted(products_dir.rglob("*")):
        relative = photo.relative_to(products_dir)
        if photo.suffix not in PHOTO_SUFFIXES or relative.parts[0] == THUMBS_DIR:
            continue
        target = products_dir / thumbnail_path(relative.as_posix())
        if target.exists():
            continue
        try:
            thumb = _encode(_open(photo.read_bytes()), THUMB_SIZE)
        except InvalidImage:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(thumb)
        made += 1
    return made
