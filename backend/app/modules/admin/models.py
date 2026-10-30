from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, UTCDateTime


class AuditLog(Base):
    """One staff action: who did what to which record, and what changed."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    # Copied at the time, so the log still reads right after the staff member is renamed.
    actor_name: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(50), index=True)
    target_type: Mapped[str] = mapped_column(String(30))
    target_id: Mapped[int | None] = mapped_column(Integer)
    # How the target read at the time: a dish name, an email, an order number.
    target_label: Mapped[str] = mapped_column(String(255), default="")
    # {field: [before, after]}; for exports, the filters used and the rows sent.
    changes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), index=True
    )
