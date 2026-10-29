"""store prices in vnd

Revision ID: a41f6b2d9c07
Revises: 7d3a9c2e5f18
Create Date: 2026-10-29 08:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a41f6b2d9c07"
down_revision: str | Sequence[str] | None = "7d3a9c2e5f18"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The fixed rate the shop already charged MoMo payments at, so every existing price and
# order total keeps exactly the VND amount customers saw and paid.
USD_TO_VND = 25000

MONEY_COLUMNS = (
    ("products", "price"),
    ("orders", "total_price"),
    ("order_items", "price_at_purchase"),
)


def upgrade() -> None:
    """Upgrade schema."""
    for table, column in MONEY_COLUMNS:
        op.execute(f"UPDATE {table} SET {column} = ROUND({column} * {USD_TO_VND})")
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                column,
                existing_type=sa.Numeric(precision=10, scale=2),
                type_=sa.BigInteger(),
                existing_nullable=False,
                postgresql_using=f"{column}::bigint",
            )


def downgrade() -> None:
    """Downgrade schema."""
    for table, column in MONEY_COLUMNS:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                column,
                existing_type=sa.BigInteger(),
                type_=sa.Numeric(precision=10, scale=2),
                existing_nullable=False,
                postgresql_using=f"ROUND({column} / {USD_TO_VND}.0, 2)",
            )
        # Postgres already converted in USING; on SQLite this does the conversion.
        if op.get_bind().dialect.name != "postgresql":
            op.execute(f"UPDATE {table} SET {column} = ROUND({column} / {USD_TO_VND}.0, 2)")
