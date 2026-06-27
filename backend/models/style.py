from __future__ import annotations

import uuid

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from models.base import Base, TimestampedModel, UUIDModel


class StyleProfile(UUIDModel, TimestampedModel, Base):
    __tablename__ = "style_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    style_params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    voice_embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    learning_rate: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_ratings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_edits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_approved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class StyleSignal(UUIDModel, TimestampedModel, Base):
    __tablename__ = "style_signals"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("style_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_draft_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    signal_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    signal_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)


class StyleRating(UUIDModel, TimestampedModel, Base):
    __tablename__ = "style_ratings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    draft_id: Mapped[str] = mapped_column(String(36), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    dimension_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
