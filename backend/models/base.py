from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, func, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid


class Base(DeclarativeBase):
    pass


class UUIDModel(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for col in inspect(self.__class__).columns:
            val = getattr(self, col.name)
            if isinstance(val, uuid.UUID):
                result[col.name] = str(val)
            elif isinstance(val, datetime):
                result[col.name] = val.isoformat()
            elif isinstance(val, (list, dict)):
                result[col.name] = val
            else:
                result[col.name] = val
        return result


class TimestampedModel(Base):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)
