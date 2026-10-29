"""clear system order event notes

Revision ID: b2e7c4a19d63
Revises: a41f6b2d9c07
Create Date: 2026-10-29 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2e7c4a19d63"
down_revision: str | Sequence[str] | None = "a41f6b2d9c07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fixed English notes the API used to write itself. Events now say who made them, so the UI
# words these in the customer's language; only notes staff typed are kept.
SYSTEM_NOTES = ("Cancelled by customer.", "MoMo payment received.", "Payment to be refunded.")


def upgrade() -> None:
    """Upgrade schema."""
    events = sa.table("order_events", sa.column("note", sa.Text))
    op.execute(events.update().where(events.c.note.in_(SYSTEM_NOTES)).values(note=""))


def downgrade() -> None:
    """Downgrade schema."""
    # The cleared notes were derivable from the event itself; nothing to restore.
