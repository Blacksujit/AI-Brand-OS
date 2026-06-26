from __future__ import annotations

import uuid

from sqlalchemy import JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampedModel, UUIDModel


class Profile(UUIDModel, TimestampedModel, Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    bio: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    website: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    location: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    preferences: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=dict
    )

    user: Mapped[User] = relationship(
        "User", back_populates="profile"
    )
