from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import utcnow
from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.core.sql import escape_like
from app.modules.admin.operations import paginate
from app.modules.admin.schemas import Page, UserCreate, UserUpdate
from app.modules.auth.service import revoke_all_sessions
from app.modules.users.models import Role, User


def list_users(
    db: Session, search: str | None, include_deactivated: bool, page: int, page_size: int
) -> Page[User]:
    query = select(User).order_by(User.id)
    if not include_deactivated:
        query = query.where(User.deleted_at.is_(None))
    if search:
        pattern = f"%{escape_like(search.strip())}%"
        query = query.where(
            or_(
                User.name.ilike(pattern, escape="\\"),
                User.email.ilike(pattern, escape="\\"),
                User.phone.ilike(pattern, escape="\\"),
            )
        )
    return paginate(db, query, page, page_size)


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.", code="user_not_found")
    return user


def _commit_unique(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "That email or phone number is already used by another account.",
            code="email_or_phone_taken",
        ) from exc


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        name=data.name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=data.role,
        email_verified_at=utcnow() if data.email_verified else None,
    )
    db.add(user)
    _commit_unique(db)
    db.refresh(user)
    return user


def update_user(db: Session, admin: User, user_id: int, data: UserUpdate) -> User:
    user = get_user(db, user_id)
    changes = data.model_dump(exclude_unset=True)

    if user.id == admin.id and changes.get("role", Role.ADMIN) != Role.ADMIN:
        raise BadRequestError("You cannot remove your own admin role.", code="cannot_demote_self")

    if "email_verified" in changes:
        verified = changes.pop("email_verified")
        if verified and user.email_verified_at is None:
            user.email_verified_at = utcnow()
        elif not verified:
            user.email_verified_at = None
    if "password" in changes:
        user.password_hash = hash_password(changes.pop("password"))
        # A staff-set password replaces whatever an intruder may have known.
        revoke_all_sessions(db, user.id)
    for field, value in changes.items():
        setattr(user, field, value)

    _commit_unique(db)
    return user


def deactivate_user(db: Session, admin: User, user_id: int) -> User:
    user = get_user(db, user_id)
    if user.id == admin.id:
        raise BadRequestError(
            "You cannot deactivate your own account.", code="cannot_deactivate_self"
        )
    if user.deleted_at is None:
        user.deleted_at = utcnow()
        revoke_all_sessions(db, user.id)
        db.commit()
    return user


def restore_user(db: Session, user_id: int) -> User:
    user = get_user(db, user_id)
    user.deleted_at = None
    db.commit()
    return user
