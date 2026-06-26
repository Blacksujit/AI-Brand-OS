from __future__ import annotations

import uuid

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampedModel, UUIDModel


class KnowledgeEntry(UUIDModel, TimestampedModel, Base):
    __tablename__ = "knowledge_entries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    source_id: Mapped[str] = mapped_column(
        String(256), nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(512), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(
        JSON, nullable=True
    )
    relevance_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )


class KnowledgeTag(UUIDModel, TimestampedModel, Base):
    __tablename__ = "knowledge_tags"

    entry_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
