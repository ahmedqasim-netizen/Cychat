from enum import Enum

from sqlalchemy import (
    ForeignKey,
    Integer,
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


class TokenStatus(int, Enum):
    ACTIVE = 1
    DISABLED = 0


class AccessTokens(Base, CommonMixin, TimestampMixin):

    __tablename__ = "access_tokens"
    __table_args__ = {"schema": "chat"}

    user_id: Mapped[int] = mapped_column("user", ForeignKey("chat.users.id"), index=True)
    token: Mapped[str] = mapped_column(String(120), index=True)
    token_status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)