from fastapi import APIRouter, BackgroundTasks, Request, Response, status

from app.core.config import get_settings
from app.core.deps import CurrentSession, CurrentUser, DbSession
from app.core.email import Mailer, send_safely
from app.core.errors import UnauthorizedError
from app.core.rate_limit import (
    CODE_ENTRY,
    LOGIN,
    LOGIN_FAILURES,
    PASSWORD_RESET_PER_EMAIL,
    PASSWORD_RESET_REQUESTS,
    REGISTER,
    VERIFICATION_EMAILS,
    client_ip,
    enforce,
    rate_limit,
    too_many_requests,
)
from app.modules.auth import service
from app.modules.auth.schemas import (
    ChangePasswordIn,
    ForgotPasswordIn,
    LoginIn,
    RegisterIn,
    ResetPasswordIn,
    UserOut,
    VerifyEmailIn,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, issued: service.IssuedSession) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        issued.token,
        # Without "remember me" the cookie dies with the browser; the server expiry still applies.
        max_age=settings.remember_me_ttl_days * 86400 if issued.session.is_persistent else None,
        httponly=True,
        samesite="lax",
        secure=not settings.is_local,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(get_settings().session_cookie_name, path="/")


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(REGISTER)],
)
def register(data: RegisterIn, db: DbSession):
    return service.register(db, data)


@router.post("/login", response_model=UserOut, dependencies=[rate_limit(LOGIN)])
def login(data: LoginIn, db: DbSession, request: Request, response: Response):
    # Always on, unlike the throughput limits: this is the brute-force guard. Even the right
    # password is refused while blocked, or the block would confirm a guess.
    limiter = request.app.state.rate_limiter
    key = f"{client_ip(request)}:{data.email}"
    wait = limiter.wait(LOGIN_FAILURES, key)
    if wait is not None:
        raise too_many_requests(wait)
    try:
        user = service.authenticate(db, data.email, data.password)
    except UnauthorizedError:
        limiter.hit(LOGIN_FAILURES, key)
        raise
    limiter.forget(LOGIN_FAILURES, key)
    _set_session_cookie(response, service.create_session(db, user, data.remember))
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(db: DbSession, user_session: CurrentSession, response: Response):
    if user_session is not None:
        service.revoke_session(db, user_session)
    _clear_session_cookie(response)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user


@router.post(
    "/password/forgot",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[rate_limit(PASSWORD_RESET_REQUESTS)],
)
def forgot_password(
    data: ForgotPasswordIn,
    db: DbSession,
    background: BackgroundTasks,
    mailer: Mailer,
    request: Request,
):
    # Also per address, so nobody can fill one person's inbox from many IPs. Counted whether
    # or not the account exists, so the limit itself does not reveal which emails are taken.
    enforce(request, PASSWORD_RESET_PER_EMAIL, f"email:{data.email}")
    email = service.start_password_reset(db, data.email, request.app.state.phantom_reset_codes)
    if email is not None:
        background.add_task(send_safely, mailer, email)
    return {"detail": "If an account exists for that email, a reset code has been sent."}


@router.post(
    "/password/reset",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[rate_limit(CODE_ENTRY)],
)
def reset_password(data: ResetPasswordIn, db: DbSession, request: Request, response: Response):
    phantoms = request.app.state.phantom_reset_codes
    service.reset_password(db, data.email, data.code, data.new_password, phantoms)
    _clear_session_cookie(response)


@router.post("/password/change", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: ChangePasswordIn, db: DbSession, user: CurrentUser, user_session: CurrentSession
):
    if user_session is None:
        raise UnauthorizedError("Please sign in to continue.", code="auth_required")
    service.change_password(db, user, user_session, data.current_password, data.new_password)


@router.post(
    "/email/verification",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[rate_limit(VERIFICATION_EMAILS, per="user")],
)
def send_email_verification(
    db: DbSession, user: CurrentUser, background: BackgroundTasks, mailer: Mailer
):
    background.add_task(send_safely, mailer, service.start_email_verification(db, user))
    return {"detail": "A verification code has been sent to your email."}


@router.post("/email/verify", response_model=UserOut, dependencies=[rate_limit(CODE_ENTRY)])
def verify_email(data: VerifyEmailIn, db: DbSession, user: CurrentUser):
    return service.verify_email(db, user, data.code)
