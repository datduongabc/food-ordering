from collections.abc import Callable
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import utcnow
from app.core.errors import ConflictError, NotFoundError
from app.modules.admin import audit
from app.modules.admin.schemas import AdminPromoOut, PromoCodeIn
from app.modules.orders.models import Order, OrderStatus
from app.modules.promotions.models import PromoCode
from app.modules.users.models import User


def _snapshot(promo: PromoCode) -> dict[str, Any]:
    return {
        "code": promo.code,
        "kind": promo.kind,
        "value": promo.value,
        "max_discount": promo.max_discount,
        "min_subtotal": promo.min_subtotal,
        "starts_on": promo.starts_on.isoformat() if promo.starts_on else None,
        "ends_on": promo.ends_on.isoformat() if promo.ends_on else None,
        "usage_limit": promo.usage_limit,
        "per_customer_limit": promo.per_customer_limit,
    }


def _out(promo: PromoCode, uses: int) -> AdminPromoOut:
    # getattr, not __dict__: attributes expired by a commit load again on access.
    fields = {name: getattr(promo, name) for name in AdminPromoOut.model_fields if name != "uses"}
    return AdminPromoOut(**fields, uses=uses)


def _uses(db: Session, promo_ids: list[int]) -> dict[int, int]:
    rows = db.execute(
        select(Order.promo_code_id, func.count(Order.id))
        .where(Order.promo_code_id.in_(promo_ids), Order.status != OrderStatus.CANCELLED)
        .group_by(Order.promo_code_id)
    ).all()
    return {promo_id: count for promo_id, count in rows}


def list_promos(db: Session) -> list[AdminPromoOut]:
    # Active codes first, newest first within each group.
    promos = db.scalars(
        select(PromoCode).order_by(PromoCode.disabled_at.is_not(None), PromoCode.id.desc())
    ).all()
    uses = _uses(db, [promo.id for promo in promos])
    return [_out(promo, uses.get(promo.id, 0)) for promo in promos]


def _get(db: Session, promo_id: int) -> PromoCode:
    promo = db.get(PromoCode, promo_id)
    if promo is None:
        raise NotFoundError("Promo code not found.", code="promo_not_found_admin")
    return promo


def get_promo(db: Session, promo_id: int) -> AdminPromoOut:
    promo = _get(db, promo_id)
    return _out(promo, _uses(db, [promo.id]).get(promo.id, 0))


def _commit_unique(db: Session, code: str, before_commit: Callable[[], None]) -> None:
    try:
        db.flush()
        before_commit()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            f'The code "{code}" already exists.', code="promo_code_taken", params={"code": code}
        ) from exc


def create_promo(db: Session, admin: User, data: PromoCodeIn) -> AdminPromoOut:
    promo = PromoCode(**data.model_dump())
    db.add(promo)
    _commit_unique(
        db,
        data.code,
        lambda: audit.record(
            db,
            admin,
            "promo.create",
            "promo",
            promo.id,
            promo.code,
            audit.created(_snapshot(promo)),
        ),
    )
    return get_promo(db, promo.id)


def update_promo(db: Session, admin: User, promo_id: int, data: PromoCodeIn) -> AdminPromoOut:
    promo = _get(db, promo_id)
    before = _snapshot(promo)
    for field, value in data.model_dump().items():
        setattr(promo, field, value)

    def log_changes() -> None:
        changed = audit.diff(before, _snapshot(promo))
        if changed:
            audit.record(db, admin, "promo.update", "promo", promo.id, promo.code, changed)

    _commit_unique(db, data.code, log_changes)
    return get_promo(db, promo.id)


def disable_promo(db: Session, admin: User, promo_id: int) -> AdminPromoOut:
    promo = _get(db, promo_id)
    if promo.disabled_at is None:
        promo.disabled_at = utcnow()
        audit.record(db, admin, "promo.disable", "promo", promo.id, promo.code)
        db.commit()
    return get_promo(db, promo.id)


def enable_promo(db: Session, admin: User, promo_id: int) -> AdminPromoOut:
    promo = _get(db, promo_id)
    if promo.disabled_at is not None:
        promo.disabled_at = None
        audit.record(db, admin, "promo.enable", "promo", promo.id, promo.code)
        db.commit()
    return get_promo(db, promo.id)
