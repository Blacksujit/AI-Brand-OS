"""Create trend tables

Revision ID: 003_trend_schema
Revises: 002_style_schema
Create Date: 2026-06-27 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # trend_signals table
    op.create_table(
        "trend_signals",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_id", sa.String(256), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("entities", sa.JSON(), nullable=True),
        sa.Column("categories", sa.JSON(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_trend_signals_source", "trend_signals", ["source_type", "source_id"], unique=True
    )
    op.create_index("ix_trend_signals_created_at", "trend_signals", ["created_at"])
    op.create_index("ix_trend_signals_relevance", "trend_signals", ["relevance_score"])

    # trend_topics table
    op.create_table(
        "trend_topics",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("signal_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("velocity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("peak_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="emerging"),
        sa.Column("representative_signals", sa.JSON(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("centroid_embedding", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trend_topics_name", "trend_topics", ["name"])
    op.create_index("ix_trend_topics_status_velocity", "trend_topics", ["status", "velocity"])

    # trend_analyses table
    op.create_table(
        "trend_analyses",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("topic_ids", sa.JSON(), nullable=False),
        sa.Column("insights", sa.Text(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("generated_for", sa.String(256), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trend_analyses_user_created", "trend_analyses", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_trend_analyses_user_created", table_name="trend_analyses")
    op.drop_table("trend_analyses")
    op.drop_index("ix_trend_topics_status_velocity", table_name="trend_topics")
    op.drop_index("ix_trend_topics_name", table_name="trend_topics")
    op.drop_table("trend_topics")
    op.drop_index("ix_trend_signals_relevance", table_name="trend_signals")
    op.drop_index("ix_trend_signals_created_at", table_name="trend_signals")
    op.drop_index("ix_trend_signals_source", table_name="trend_signals")
    op.drop_table("trend_signals")
