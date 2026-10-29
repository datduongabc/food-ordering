import hmac
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.email import Email
from app.core.errors import (
    BadRequestError,
    ConflictError,
    TooManyRequestsError,
    UnauthorizedError,
)
from app.core.security import (
    hash_otp_code,
    hash_password,
    hash_token,
    new_otp_code,
    new_session_token,
    verify_password,
)
from app.modules.auth.models import OtpCode, OtpPurpose, UserSession
from app.modules.auth.phantom import PhantomResetCodes
from app.modules.auth.schemas import RegisterIn
from app.modules.users.models import User

INVALID_CREDENTIALS = "Email or password is incorrect."
INVALID_CODE = "The code is invalid or has expired. Request a new one."

# Verified against when the email is unknown, so response time does not reveal which accounts exist.
_DUMMY_HASH = hash_password("timing-equaliser-password")


@dataclass(frozen=True)
class IssuedSession:
    token: str
    session: UserSession


def get_active_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email, User.deleted_at.is_(None)))


def register(db: Session, data: RegisterIn) -> User:
    existing = db.scalar(
        select(User).where(or_(User.email == data.email, User.phone == data.phone))
    )
    if existing is not None:
        if existing.email == data.email:
            raise ConflictError("Email already registered.", code="email_taken")
        raise ConflictError("Phone number already registered.", code="phone_taken")

    user = User(
        name=data.name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = get_active_user_by_email(db, email)
    if user is None:
        verify_password(password, _DUMMY_HASH)
        raise UnauthorizedError(INVALID_CREDENTIALS, code="invalid_credentials")

    valid, upgraded_hash = verify_password(password, user.password_hash)
    if not valid:
        raise UnauthorizedError(INVALID_CREDENTIALS, code="invalid_credentials")

    if upgraded_hash:
        user.password_hash = upgraded_hash
        db.commit()
    return user


def create_session(db: Session, user: User, remember: bool) -> IssuedSession:
    settings = get_settings()
    ttl = (
        timedelta(days=settings.remember_me_ttl_days)
        if remember
        else timedelta(hours=settings.session_ttl_hours)
    )
    token = new_session_token()
    user_session = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        is_persistent=remember,
        expires_at=utcnow() + ttl,
    )
    db.add(user_session)
    db.commit()
    return IssuedSession(token=token, session=user_session)


def revoke_session(db: Session, user_session: UserSession) -> None:
    db.delete(user_session)
    db.commit()


def revoke_all_sessions(db: Session, user_id: int, keep_session_id: int | None = None) -> None:
    stmt = delete(UserSession).where(UserSession.user_id == user_id)
    if keep_session_id is not None:
        stmt = stmt.where(UserSession.id != keep_session_id)
    db.execute(stmt)


def issue_otp(db: Session, user: User, purpose: OtpPurpose) -> str:
    """Replaces any previous code for this purpose, so only the latest emailed code works."""
    settings = get_settings()
    db.execute(delete(OtpCode).where(OtpCode.user_id == user.id, OtpCode.purpose == purpose))
    code = new_otp_code()
    db.add(
        OtpCode(
            user_id=user.id,
            purpose=purpose,
            code_hash=hash_otp_code(code),
            expires_at=utcnow() + timedelta(minutes=settings.otp_ttl_minutes),
        )
    )
    db.commit()
    return code


def _too_many_code_attempts() -> TooManyRequestsError:
    return TooManyRequestsError(
        "Too many incorrect codes. Request a new one.", code="too_many_code_attempts"
    )


def consume_otp(db: Session, user: User, purpose: OtpPurpose, code: str) -> None:
    settings = get_settings()
    otp = db.scalar(select(OtpCode).where(OtpCode.user_id == user.id, OtpCode.purpose == purpose))
    if otp is None or otp.expires_at <= utcnow():
        raise BadRequestError(INVALID_CODE, code="invalid_code")
    if otp.attempts >= settings.otp_max_attempts:
        raise _too_many_code_attempts()

    if not hmac.compare_digest(otp.code_hash, hash_otp_code(code)):
        otp.attempts += 1
        db.commit()
        raise BadRequestError(INVALID_CODE, code="invalid_code")

    db.delete(otp)


def otp_email(user: User, purpose: OtpPurpose, code: str) -> Email:
    settings = get_settings()
    subject, intro = {
        OtpPurpose.PASSWORD_RESET: (
            "Reset your DaTeNO password",
            "Use this code to reset your password:",
        ),
        OtpPurpose.EMAIL_VERIFICATION: (
            "Verify your DaTeNO email",
            "Use this code to verify your email address:",
        ),
    }[purpose]
    text = (
        f"Hi {user.name},\n\n{intro}\n\n    {code}\n\n"
        f"The code expires in {settings.otp_ttl_minutes} minutes. "
        "If you did not request it, you can ignore this email.\n\nDaTeNO Restaurant"
    )
    return Email(to=user.email, subject=subject, text=text)


def start_password_reset(db: Session, email: str, phantoms: PhantomResetCodes) -> Email | None:
    """Returns the email to send, or None for unknown accounts (the caller responds identically)."""
    user = get_active_user_by_email(db, email)
    if user is None:
        phantoms.issue(email)
        return None
    code = issue_otp(db, user, OtpPurpose.PASSWORD_RESET)
    return otp_email(user, OtpPurpose.PASSWORD_RESET, code)


def reset_password(
    db: Session, email: str, code: str, new_password: str, phantoms: PhantomResetCodes
) -> None:
    user = get_active_user_by_email(db, email)
    if user is None:
        if not phantoms.record_guess(email):
            raise _too_many_code_attempts()
        raise BadRequestError(INVALID_CODE, code="invalid_code")
    consume_otp(db, user, OtpPurpose.PASSWORD_RESET, code)
    user.password_hash = hash_password(new_password)
    # Whoever triggered the reset may be locking out an attacker, so every session goes.
    revoke_all_sessions(db, user.id)
    db.commit()


def change_password(
    db: Session, user: User, current_session: UserSession, current: str, new: str
) -> None:
    valid, _ = verify_password(current, user.password_hash)
    if not valid:
        raise BadRequestError("Current password is incorrect.", code="wrong_current_password")
    user.password_hash = hash_password(new)
    revoke_all_sessions(db, user.id, keep_session_id=current_session.id)
    db.commit()


def start_email_verification(db: Session, user: User) -> Email:
    if user.is_email_verified:
        raise BadRequestError("Your email is already verified.", code="email_already_verified")
    code = issue_otp(db, user, OtpPurpose.EMAIL_VERIFICATION)
    return otp_email(user, OtpPurpose.EMAIL_VERIFICATION, code)


def verify_email(db: Session, user: User, code: str) -> User:
    if user.is_email_verified:
        return user
    consume_otp(db, user, OtpPurpose.EMAIL_VERIFICATION, code)
    user.email_verified_at = utcnow()
    db.commit()
    return user
