"""drop account lockout

Revision ID: d7a3f9b2e415
Revises: c5d1e8f3a274
Create Date: 2026-10-29 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7a3f9b2e415"
down_revision: str | Sequence[str] | None = "c5d1e8f3a274"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Sign-in failures are now counted per address and email in the rate limiter, which also
    # covers unknown emails; a per-account lock revealed which accounts exist.
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint(op.f("ck_users_failed_login_attempts"), type_="check")
        batch_op.drop_column("locked_until")
        batch_op.drop_column("failed_login_attempts")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "failed_login_attempts", sa.SmallInteger(), server_default="0", nullable=False
            )
        )
        batch_op.add_column(sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_check_constraint(
            op.f("ck_users_failed_login_attempts"), "failed_login_attempts >= 0"
        )
