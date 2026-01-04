from enum import Enum
from sqlalchemy import (
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from typing import (
    Optional,
)

from app.utils.mixins import (
    Base,
    CommonMixin,
    TimestampMixin,
)


class ChatStatus(str, Enum):
    online = "online"
    offline = "offline"
    busy = "busy"
    dont_disturb = "don't disturb"


class UserRole(str, Enum):

    user = "user"
    admin = "admin"


class Users(Base, CommonMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = {"schema": "chat"}

    nickname: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(String(120), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    user_role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    public_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)