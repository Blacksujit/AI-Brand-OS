from __future__ import annotations

import uuid

from sqlalchemy import JSON, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampedModel, UUIDModel


class TrendSignal(UUIDModel, TimestampedModel, Base):
    __tablename__ = "trend_signals"

    source_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(256), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    entities: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    categories: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_trend_signals_source", "source_type", "source_id", unique=True),
        Index("ix_trend_signals_created_at", "created_at"),
        Index("ix_trend_signals_relevance", "relevance_score"),
    )


class TrendTopic(UUIDModel, TimestampedModel, Base):
    __tablename__ = "trend_topics"

    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    signal_count: Mapped[int] = mapped_column(Integer, default=0)
    velocity: Mapped[float] = mapped_column(Float, default=0.0)
    peak_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="emerging", nullable=False, index=True)
    representative_signals: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    centroid_embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (Index("ix_trend_topics_status_velocity", "status", "velocity"),)


class TrendAnalysis(UUIDModel, TimestampedModel, Base):
    __tablename__ = "trend_analyses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    insights: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    generated_for: Mapped[str | None] = mapped_column(String(256), nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (Index("ix_trend_analyses_user_created", "user_id", "created_at"),)
