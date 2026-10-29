from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db, utcnow
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import hash_token
from app.modules.auth.models import UserSession
from app.modules.users.models import User

DbSession = Annotated[Session, Depends(get_db)]


def get_current_session(
    db: DbSession,
    session_token: Annotated[
        str | None, Cookie(alias=get_settings().session_cookie_name, include_in_schema=False)
    ] = None,
) -> UserSession | None:
    if not session_token:
        return None
    user_session = db.scalar(
        select(UserSession).where(UserSession.token_hash == hash_token(session_token))
    )
    if user_session is None or user_session.expires_at <= utcnow():
        return None
    # Re-checked on every request so deactivation and role changes apply immediately.
    if user_session.user.deleted_at is not None:
        return None
    return user_session


CurrentSession = Annotated[UserSession | None, Depends(get_current_session)]


def get_optional_user(user_session: CurrentSession) -> User | None:
    return user_session.user if user_session else None


def get_current_user(user: Annotated[User | None, Depends(get_optional_user)]) -> User:
    if user is None:
        raise UnauthorizedError("Please sign in to continue.")
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_admin:
        raise ForbiddenError("Administrator access required.")
    return user


OptionalUser = Annotated[User | None, Depends(get_optional_user)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
