"""derive location map url from address

Revision ID: 5c2d8f1a7b34
Revises: e99ccedae87d
Create Date: 2026-10-29 06:00:00.000000

"""

from collections.abc import Sequence
from urllib.parse import urlencode

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c2d8f1a7b34"
down_revision: str | Sequence[str] | None = "e99ccedae87d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # The API now builds the link from the address; the stored short links were dead.
    with op.batch_alter_table("locations") as batch_op:
        batch_op.drop_column("map_url")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("locations") as batch_op:
        batch_op.add_column(sa.Column("map_url", sa.Text(), nullable=True))

    locations = sa.table(
        "locations", sa.column("id", sa.Integer), sa.column("address"), sa.column("map_url")
    )
    bind = op.get_bind()
    for location_id, address in bind.execute(sa.select(locations.c.id, locations.c.address)):
        url = "https://www.google.com/maps/search/?" + urlencode({"api": "1", "query": address})
        bind.execute(locations.update().where(locations.c.id == location_id).values(map_url=url))

    with op.batch_alter_table("locations") as batch_op:
        batch_op.alter_column("map_url", existing_type=sa.Text(), nullable=False)
