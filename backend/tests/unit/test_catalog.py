from types import SimpleNamespace

import pytest

from app.core.sql import escape_like
from app.modules.catalog.schemas import ProductOut


@pytest.mark.parametrize(
    ("term", "escaped"),
    [
        ("pho", "pho"),
        ("50%", "50\\%"),
        ("a_b", "a\\_b"),
        ("back\\slash", "back\\\\slash"),
        ("%_\\", "\\%\\_\\\\"),
    ],
)
def test_escape_like(term, escaped):
    assert escape_like(term) == escaped


def test_product_out_exposes_public_image_url_not_storage_path():
    product = SimpleNamespace(
        id=1,
        name={"vi": "Phở bò", "en": "Pho Bo"},
        slug="pho-bo",
        description={"vi": "Phở bò tái", "en": "Beef noodle soup"},
        price=120_000,
        average_rating=None,
        category=None,
        locations=[],
        image_url="main_dishes/pho_bo.webp",
    )

    data = ProductOut.model_validate(product).model_dump()

    assert data["image_url"] == "/media/products/main_dishes/pho_bo.webp"
    assert "image_path" not in data
