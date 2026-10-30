"""accent-blind search

Revision ID: d0496976bdfc
Revises: d62b1c5bbf09
Create Date: 2026-10-30 03:00:00.000000

"""

import unicodedata
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d0496976bdfc"
down_revision: str | Sequence[str] | None = "d62b1c5bbf09"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def fold(text: str) -> str:
    # A frozen copy of app.core.text.fold, so this migration keeps meaning what it did.
    decomposed = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    bare = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(bare.casefold().split())


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "products", sa.Column("search_text", sa.Text(), server_default="", nullable=False)
    )
    op.add_column("users", sa.Column("search_text", sa.Text(), server_default="", nullable=False))

    db = op.get_bind()
    products = sa.table(
        "products",
        sa.column("id"),
        sa.column("name_vi"),
        sa.column("name_en"),
        sa.column("search_text"),
    )
    for row in db.execute(sa.select(products.c.id, products.c.name_vi, products.c.name_en)):
        db.execute(
            products.update()
            .where(products.c.id == row.id)
            .values(search_text=fold(f"{row.name_vi} {row.name_en}"))
        )
    users = sa.table(
        "users",
        sa.column("id"),
        sa.column("name"),
        sa.column("email"),
        sa.column("phone"),
        sa.column("search_text"),
    )
    for row in db.execute(sa.select(users.c.id, users.c.name, users.c.email, users.c.phone)):
        db.execute(
            users.update()
            .where(users.c.id == row.id)
            .values(search_text=fold(f"{row.name} {row.email} {row.phone}"))
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "search_text")
    op.drop_column("products", "search_text")
