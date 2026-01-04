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


class MessageStatus(int, Enum):


    READ = 1 
    NOT_READ = 0


class Messages(Base, CommonMixin, TimestampMixin):

    __tablename__ = "messages"
    __table_args__ = {"schema": "chat"}

    sender: Mapped[int] = mapped_column(ForeignKey("chat.users.id"), index=True, nullable=False)
    receiver: Mapped[int] = mapped_column(ForeignKey("chat.users.id"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(String(1024), nullable=False)
    message_type: Mapped[str] = mapped_column(String(10), nullable=False, default="text")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=MessageStatus.NOT_READ.value)
    room: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    media: Mapped[Optional[str]] = mapped_column(String(220), nullable=True)