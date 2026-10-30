"""Real image files for upload tests, made with Pillow."""

import io

from PIL import Image


def photo(
    fmt: str = "PNG",
    size: tuple[int, int] = (640, 480),
    *,
    mode: str = "RGB",
    orientation: int | None = None,
    gps: bool = False,
) -> bytes:
    image = Image.new(mode, size, "orange" if mode != "1" else 1)
    # A darker left half, so a rotation shows up in the pixels as well as the size.
    if mode == "RGB":
        image.paste((40, 20, 10), (0, 0, size[0] // 2, size[1]))
    exif = Image.Exif()
    if orientation:
        exif[0x0112] = orientation
    if gps:
        exif[0x8825] = {1: "N", 2: (10.0, 46.0, 30.0), 3: "E", 4: (106.0, 42.0, 0.0)}
    out = io.BytesIO()
    image.save(out, fmt, exif=exif) if (orientation or gps) else image.save(out, fmt)
    return out.getvalue()


def opened(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))
