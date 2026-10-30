import io

import pytest
from sqlalchemy import select

from app import cli
from app.core.security import verify_password
from app.modules.users.models import Role, User
from tests.photos import opened, photo


@pytest.fixture
def run_cli(db_session_factory, monkeypatch):
    """Runs `python -m app.cli` against the test database, piping `password` on stdin."""
    monkeypatch.setattr(cli, "SessionLocal", db_session_factory)

    def run(*args: str, password: str = "quan-ly-123") -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO(f"{password}\n"))
        cli.main(list(args))

    return run


ADMIN_ARGS = (
    "create-admin",
    "--email",
    " Ha@Example.com ",
    "--name",
    "Quản lý Hà",
    "--phone",
    "0911222333",
)


def test_create_admin_makes_a_verified_admin(run_cli, db, capsys):
    run_cli(*ADMIN_ARGS)

    user = db.scalar(select(User).where(User.email == "ha@example.com"))
    assert user is not None
    assert user.role == Role.ADMIN
    assert user.is_email_verified
    assert verify_password("quan-ly-123", user.password_hash)[0]
    assert f"Created admin #{user.id} <ha@example.com>" in capsys.readouterr().out


def test_create_admin_refuses_a_short_password(run_cli, db):
    with pytest.raises(SystemExit, match="at least 8 characters"):
        run_cli(*ADMIN_ARGS, password="short")

    assert db.scalar(select(User)) is None


def test_create_admin_refuses_a_taken_email_or_phone(run_cli):
    run_cli(*ADMIN_ARGS)

    with pytest.raises(SystemExit, match="already exists"):
        run_cli(
            "create-admin", "--email", "other@example.com", "--name", "B", "--phone", "0911222333"
        )


def test_thumbnails_are_made_once_for_every_photo(media_dir, capsys):
    products = media_dir / "products"
    (products / "starters").mkdir()
    (products / "starters" / "rolls.webp").write_bytes(photo("WEBP", (1200, 900)))
    (products / "uploads").mkdir()
    # An upload from before uploads were converted keeps its format; its thumbnail is WebP.
    (products / "uploads" / "old.jpg").write_bytes(photo("JPEG", (800, 800)))
    (products / "uploads" / "broken.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (products / "CREDITS.md").write_text("credits")

    cli.main(["thumbnails"])
    cli.main(["thumbnails"])

    assert capsys.readouterr().out.splitlines() == ["Made 2 thumbnail(s)", "Made 0 thumbnail(s)"]
    assert opened((products / "thumbs/starters/rolls.webp").read_bytes()).size == (640, 480)
    assert opened((products / "thumbs/uploads/old.webp").read_bytes()).size == (640, 640)
    assert not (products / "thumbs/uploads/broken.webp").exists()
