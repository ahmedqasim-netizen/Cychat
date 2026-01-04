from sqlalchemy import (
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.utils.mixins import (
    Base,
    CommonMixin,
    TimestampMixin,
)


class Contacts(Base, CommonMixin, TimestampMixin):
    __tablename__ = "contacts"
    __table_args__ = {"schema": "chat"}

    user_id: Mapped[int] = mapped_column("user", ForeignKey("chat.users.id"), index=True, nullable=False)
    contact_id: Mapped[int] = mapped_column("contact", ForeignKey("chat.users.id"), index=True, nullable=False)