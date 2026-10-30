"""promo codes

Revision ID: 30b9ab2e6605
Revises: d0496976bdfc
Create Date: 2026-10-30 02:52:28.955336

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "30b9ab2e6605"
down_revision: str | Sequence[str] | None = "d0496976bdfc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "promo_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("PERCENT", "AMOUNT", name="discount_kind", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("value", sa.BigInteger(), nullable=False),
        sa.Column("max_discount", sa.BigInteger(), nullable=True),
        sa.Column("min_subtotal", sa.BigInteger(), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=True),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("usage_limit", sa.Integer(), nullable=True),
        sa.Column("per_customer_limit", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("value > 0", name=op.f("ck_promo_codes_value")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_promo_codes")),
        sa.UniqueConstraint("code", name=op.f("uq_promo_codes_code")),
    )
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("subtotal_price", sa.BigInteger(), server_default="0", nullable=False)
        )
        batch_op.add_column(
            sa.Column("discount_amount", sa.BigInteger(), server_default="0", nullable=False)
        )
        batch_op.add_column(sa.Column("promo_code_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("promo_code", sa.String(length=32), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_orders_promo_code_id"), ["promo_code_id"], unique=False
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_orders_promo_code_id_promo_codes"),
            "promo_codes",
            ["promo_code_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # Orders placed before promo codes had nothing taken off.
    op.execute("UPDATE orders SET subtotal_price = total_price")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_orders_promo_code_id_promo_codes"), type_="foreignkey"
        )
        batch_op.drop_index(batch_op.f("ix_orders_promo_code_id"))
        batch_op.drop_column("promo_code")
        batch_op.drop_column("promo_code_id")
        batch_op.drop_column("discount_amount")
        batch_op.drop_column("subtotal_price")

    op.drop_table("promo_codes")
