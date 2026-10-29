from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.modules.catalog.schemas import ProductOut
from app.modules.catalog.service import _escape_like


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
    assert _escape_like(term) == escaped


def test_product_out_exposes_public_image_url_not_storage_path():
    product = SimpleNamespace(
        id=1,
        name="Pho Bo",
        slug="pho-bo",
        description="Beef noodle soup",
        price=Decimal("12.00"),
        average_rating=None,
        category=None,
        locations=[],
        image_url="main_dishes/pho_bo.webp",
    )

    data = ProductOut.model_validate(product).model_dump()

    assert data["image_url"] == "/media/products/main_dishes/pho_bo.webp"
    assert "image_path" not in data
