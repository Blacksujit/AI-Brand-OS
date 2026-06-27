"""create style_profiles, style_signals, style_ratings

Revision ID: 002
Revises: 001
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "style_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("style_params", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("voice_embedding", sa.JSON, nullable=True),
        sa.Column("learning_rate", sa.Float, nullable=False, server_default=sa.text("0.1")),
        sa.Column("confidence", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("total_ratings", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("total_edits", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("total_approved", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "style_signals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(36),
            sa.ForeignKey("style_profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("source_draft_id", sa.String(36), nullable=True),
        sa.Column("signal_type", sa.String(32), nullable=False, index=True),
        sa.Column("signal_data", sa.JSON, nullable=True),
        sa.Column("weight", sa.Float, nullable=False, server_default=sa.text("1.0")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_signals_profile_time", "style_signals", ["profile_id", "created_at"])
    op.create_index(
        "idx_signals_profile_type_time",
        "style_signals",
        ["profile_id", "signal_type", "created_at"],
    )
    op.create_table(
        "style_ratings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("draft_id", sa.String(36), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("dimension_scores", sa.JSON, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_ratings_user", "style_ratings", ["user_id"])
    op.create_index("idx_ratings_draft", "style_ratings", ["draft_id"])
    op.create_unique_constraint("uq_ratings_user_draft", "style_ratings", ["user_id", "draft_id"])


def downgrade() -> None:
    op.drop_constraint("uq_ratings_user_draft", "style_ratings")
    op.drop_index("idx_ratings_user", table_name="style_ratings")
    op.drop_index("idx_ratings_draft", table_name="style_ratings")
    op.drop_table("style_ratings")
    op.drop_index("idx_signals_profile_type_time", table_name="style_signals")
    op.drop_index("idx_signals_profile_time", table_name="style_signals")
    op.drop_table("style_signals")
    op.drop_table("style_profiles")
