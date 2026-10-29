"""Admin tasks: `uv run python -m app.cli create-admin --email ... --name ... --phone ...`

The password is prompted for, or read from stdin when piped (e.g. in deploy scripts).
"""

import argparse
import getpass
import sys

from sqlalchemy import or_, select

from app.core.db import SessionLocal, utcnow
from app.core.security import hash_password
from app.modules.users.models import Role, User


def create_admin(email: str, name: str, phone: str, password: str) -> User:
    with SessionLocal() as db:
        email = email.strip().lower()
        if db.scalar(select(User).where(or_(User.email == email, User.phone == phone))):
            raise SystemExit("A user with that email or phone already exists.")
        user = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            role=Role.ADMIN,
            email_verified_at=utcnow(),
        )
        db.add(user)
        db.commit()
        return user


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser("create-admin", help="Create an administrator account")
    admin.add_argument("--email", required=True)
    admin.add_argument("--name", required=True)
    admin.add_argument("--phone", required=True)
    args = parser.parse_args(argv)

    # Prompted (or piped in by scripts) rather than passed as a flag, so the password never
    # lands in shell history or the process list.
    if sys.stdin.isatty():
        password = getpass.getpass("Password (min 8 chars): ")
    else:
        password = sys.stdin.readline().rstrip("\n")
    if len(password) < 8:
        sys.exit("Password must be at least 8 characters.")
    user = create_admin(args.email, args.name, args.phone, password)
    print(f"Created admin #{user.id} <{user.email}>")


if __name__ == "__main__":
    main()
