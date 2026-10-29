"""one review per user per product

Revision ID: 9718800ed61e
Revises: 3b1c7e9a0d52
Create Date: 2026-10-29 02:24:28.027284

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9718800ed61e"
down_revision: str | Sequence[str] | None = "3b1c7e9a0d52"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Batch mode: SQLite cannot add a constraint to an existing table in place.
    with op.batch_alter_table("reviews") as batch_op:
        batch_op.create_unique_constraint("uq_reviews_user_product", ["user_id", "product_id"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("reviews") as batch_op:
        batch_op.drop_constraint("uq_reviews_user_product", type_="unique")
