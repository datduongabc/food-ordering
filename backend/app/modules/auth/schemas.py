from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.modules.users.models import Role

NormalizedEmail = Annotated[EmailStr, AfterValidator(lambda v: v.lower())]
Password = Annotated[str, Field(min_length=8, max_length=128)]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{10}$")]
OtpCodeStr = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{6}$")]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class RegisterIn(BaseModel):
    name: Name
    email: NormalizedEmail
    password: Password
    phone: Phone


class LoginIn(BaseModel):
    email: NormalizedEmail
    # No length rule here: a too-short password should fail as "incorrect", not as validation.
    password: Annotated[str, Field(min_length=1, max_length=128)]
    remember: bool = False


class ForgotPasswordIn(BaseModel):
    email: NormalizedEmail


class ResetPasswordIn(BaseModel):
    email: NormalizedEmail
    code: OtpCodeStr
    new_password: Password


class ChangePasswordIn(BaseModel):
    current_password: Annotated[str, Field(min_length=1, max_length=128)]
    new_password: Password


class VerifyEmailIn(BaseModel):
    code: OtpCodeStr


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: str
    role: Role
    is_email_verified: bool
    created_at: datetime
