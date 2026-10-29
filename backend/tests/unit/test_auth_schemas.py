import pytest
from pydantic import ValidationError

from app.modules.auth.schemas import LoginIn, RegisterIn, ResetPasswordIn

VALID = {
    "name": "  Nguyen Van A  ",
    "email": "A@Example.COM",
    "password": "correct-horse",
    "phone": "0901234567",
}


def test_register_normalises_name_and_email():
    data = RegisterIn(**VALID)

    assert data.name == "Nguyen Van A"
    assert data.email == "a@example.com"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "   "),
        ("email", "not-an-email"),
        ("password", "short"),
        ("password", "x" * 129),
        ("phone", "12345"),
        ("phone", "09012345ab"),
        ("phone", "09012345678"),
    ],
)
def test_register_rejects_invalid_field(field, value):
    with pytest.raises(ValidationError):
        RegisterIn(**{**VALID, field: value})


def test_login_accepts_short_password_so_it_fails_as_incorrect_credentials():
    assert LoginIn(email="a@example.com", password="x").remember is False


@pytest.mark.parametrize("code", ["12345", "1234567", "abcdef", ""])
def test_reset_rejects_malformed_codes(code):
    with pytest.raises(ValidationError):
        ResetPasswordIn(email="a@example.com", code=code, new_password="new-password")
