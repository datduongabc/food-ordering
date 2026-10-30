"""The staff audit log. Entries join the caller's transaction, so an action and its record
are saved together or not at all."""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.admin.models import AuditLog
from app.modules.admin.pagination import paginate
from app.modules.admin.schemas import Page
from app.modules.users.models import User

# Recorded instead of the value: the log must never hold a password, even hashed.
REDACTED = "••••••"


def record(
    db: Session,
    actor: User,
    action: str,
    target_type: str,
    target_id: int | None,
    target_label: str = "",
    changes: Mapping[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_id=actor.id,
            actor_name=actor.name,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_label=target_label[:255],
            changes=dict(changes or {}),
        )
    )


def diff(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, list[Any]]:
    """The fields whose value changed, as {field: [before, after]}."""
    return {
        key: [before.get(key), value] for key, value in after.items() if before.get(key) != value
    }


def created(snapshot: Mapping[str, Any]) -> dict[str, list[Any]]:
    return {key: [None, value] for key, value in snapshot.items()}


def list_entries(
    db: Session,
    action: str | None,
    target_type: str | None,
    target_id: int | None,
    page: int,
    page_size: int,
) -> Page[AuditLog]:
    query = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    if action:
        # "product" matches every product action; "product.update" only that one.
        query = query.where(
            (AuditLog.action == action) | AuditLog.action.startswith(f"{action}.", autoescape=True)
        )
    if target_type:
        query = query.where(AuditLog.target_type == target_type)
    if target_id is not None:
        query = query.where(AuditLog.target_id == target_id)
    return paginate(db, query, page, page_size)
