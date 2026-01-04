from sqlalchemy import (
    ForeignKey,
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


class Rooms(Base, CommonMixin, TimestampMixin):
    __tablename__ = "rooms"
    __table_args__ = {"schema": "chat"}

    room_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)


class RoomMembers(Base, CommonMixin, TimestampMixin):
    __tablename__ = "room_members"
    __table_args__ = {"schema": "chat"}

    room_id: Mapped[int] = mapped_column("room", ForeignKey("chat.rooms.id"), nullable=False, index=True)
    member_id: Mapped[int] = mapped_column("member", ForeignKey("chat.users.id"), nullable=False, index=True)
    encrypted_room_key: Mapped[Optional[str]] = mapped_column(String(4000), nullable=True)
    key_provider_id: Mapped[Optional[int]] = mapped_column("key_provider", ForeignKey("chat.users.id"), nullable=True)