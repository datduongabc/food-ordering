import pytest

from app.core.text import fold


@pytest.mark.parametrize(
    ("text", "folded"),
    [
        ("Phở bò", "pho bo"),
        ("BÒ BÍT TẾT", "bo bit tet"),
        ("Đậu hũ chiên", "dau hu chien"),
        ("Nguyễn  Thị\tẢnh", "nguyen thi anh"),
        ("Crab, Corn & Chicken Soup", "crab, corn & chicken soup"),
        # Some keyboards send precomposed letters and some combining marks; both fold alike.
        ("Phở", "pho"),
    ],
)
def test_fold_drops_accents_case_and_extra_spaces(text, folded):
    assert fold(text) == folded
