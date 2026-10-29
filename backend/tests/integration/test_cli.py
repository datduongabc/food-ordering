import io

import pytest
from sqlalchemy import select

from app import cli
from app.core.security import verify_password
from app.modules.users.models import Role, User


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
