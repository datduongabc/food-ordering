"""pg_trgm GIN search indexes and reservation slot composite index

Revision ID: 8f4e2a1c9b07
Revises: 4dae6b68695b
Create Date: 2026-11-03 01:35:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f4e2a1c9b07"
down_revision: str | Sequence[str] | None = "4dae6b68695b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ix_reservations_location_date_time",
        "reservations",
        ["location_id", "reservation_date", "reservation_time"],
        unique=False,
    )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_products_search_text_trgm "
            "ON products USING gin (search_text gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_users_search_text_trgm "
            "ON users USING gin (search_text gin_trgm_ops)"
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_users_search_text_trgm")
        op.execute("DROP INDEX IF EXISTS ix_products_search_text_trgm")
    op.drop_index("ix_reservations_location_date_time", table_name="reservations")
