import datetime
import re
from sqlalchemy import (
    BIGINT,
    DateTime,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declarative_mixin,
    declared_attr,
    mapped_column,
)


class Base(DeclarativeBase):

    __abstract__ = True

    __allow_unmapped__ = True


@declarative_mixin
class CommonMixin:


    __name__: str

    __table_args__ = {"schema": "chat"}
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)

    @declared_attr
    def __tablename__(cls) -> str:
        split_cap = re.findall("[A-Z][^A-Z]*", cls.__name__)
        table_name = (
            "".join(map(lambda word: word.lower() + "_", split_cap[:-1]))
            + split_cap[-1].lower()
        )
        return table_name


@declarative_mixin
class TimestampMixin:
    creation_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    modified_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )