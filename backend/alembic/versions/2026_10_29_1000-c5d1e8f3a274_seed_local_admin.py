"""seed local admin

Revision ID: c5d1e8f3a274
Revises: b2e7c4a19d63
Create Date: 2026-10-29 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.core.config import get_settings

# revision identifiers, used by Alembic.
revision: str = "c5d1e8f3a274"
down_revision: str | Sequence[str] | None = "b2e7c4a19d63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The admin the PHP app shipped with, so a fresh local database can be signed into at once.
# Its password is public, so it is only seeded outside production; there, use `create-admin`.
ADMIN_EMAIL = "datduongtandat385@gmail.com"
ADMIN_PHONE = "0819152362"
# argon2id of "12345678"; hashed here because migrations must not depend on app code.
ADMIN_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$jxfrDyuX2o5lWSJTwzFAWg"
    "$plJBP4OKzLxemoF3FzD2GYOMQ5xc7FKCrfbCceHPWCc"
)

users = sa.table(
    "users",
    sa.column("name", sa.String),
    sa.column("email", sa.String),
    sa.column("password_hash", sa.String),
    sa.column("role", sa.String),
    sa.column("phone", sa.String),
    sa.column("email_verified_at", sa.DateTime(timezone=True)),
    sa.column("failed_login_attempts", sa.SmallInteger),
)


def upgrade() -> None:
    """Upgrade schema."""
    if not get_settings().is_local:
        return
    taken = op.get_bind().scalar(
        sa.select(sa.func.count())
        .select_from(users)
        .where(sa.or_(users.c.email == ADMIN_EMAIL, users.c.phone == ADMIN_PHONE))
    )
    if taken:
        return
    op.execute(
        users.insert().values(
            name="Quản trị viên",
            email=ADMIN_EMAIL,
            password_hash=ADMIN_PASSWORD_HASH,
            role="ADMIN",
            phone=ADMIN_PHONE,
            email_verified_at=sa.func.now(),
            failed_login_attempts=0,
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Orders keep their customer (RESTRICT), so a seed admin who has ordered stays.
    orders = sa.table("orders", sa.column("user_id", sa.Integer))
    users_id = sa.table("users", sa.column("id", sa.Integer), sa.column("email", sa.String))
    op.execute(
        users_id.delete().where(
            users_id.c.email == ADMIN_EMAIL,
            ~sa.exists().where(orders.c.user_id == users_id.c.id),
        )
    )
