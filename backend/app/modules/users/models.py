from datetime import datetime
from enum import StrEnum

from sqlalchemy import Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, UTCDateTime


class Role(StrEnum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role", native_enum=False, length=20), default=Role.CUSTOMER
    )
    phone: Mapped[str] = mapped_column(String(10), unique=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN
