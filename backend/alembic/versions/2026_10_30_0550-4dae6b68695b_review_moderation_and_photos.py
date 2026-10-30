"""review moderation, photos and verified purchases

Revision ID: 4dae6b68695b
Revises: 5c2e8a91d7f3
Create Date: 2026-10-30 05:50:56.989818

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4dae6b68695b"
down_revision: str | Sequence[str] | None = "5c2e8a91d7f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "review_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("review_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["reviews.id"],
            name=op.f("fk_review_photos_review_id_reviews"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_photos")),
    )
    op.create_index(
        op.f("ix_review_photos_review_id"), "review_photos", ["review_id"], unique=False
    )
    op.add_column(
        "products", sa.Column("review_count", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column(
        "reviews",
        sa.Column("verified_purchase", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("reviews", sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reviews", sa.Column("reply", sa.Text(), nullable=True))
    op.add_column("reviews", sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True))

    # Reviews written before purchases were required keep their place; those whose author
    # did have a delivered order of the dish get the badge.
    op.execute(
        """
        UPDATE reviews SET verified_purchase = TRUE
        WHERE EXISTS (
            SELECT 1 FROM orders JOIN order_items ON order_items.order_id = orders.id
            WHERE orders.user_id = reviews.user_id
              AND orders.status = 'COMPLETED'
              AND order_items.product_id = reviews.product_id
        )
        """
    )
    op.execute(
        """
        UPDATE products SET review_count = (
            SELECT COUNT(*) FROM reviews WHERE reviews.product_id = products.id
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("reviews", schema=None) as batch_op:
        batch_op.drop_column("replied_at")
        batch_op.drop_column("reply")
        batch_op.drop_column("hidden_at")
        batch_op.drop_column("verified_purchase")
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_column("review_count")
    op.drop_index(op.f("ix_review_photos_review_id"), table_name="review_photos")
    op.drop_table("review_photos")
