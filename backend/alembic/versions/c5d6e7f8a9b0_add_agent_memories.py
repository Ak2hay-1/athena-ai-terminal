"""Add agent_memories table for orchestrator trading intelligence."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.database.migration_helpers import has_index
from app.database.migration_helpers import has_table

revision = "c5d6e7f8a9b0"
down_revision = "b4c5d6e7f8a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not has_table("agent_memories"):
        op.create_table(
            "agent_memories",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("agent_id", sa.String(length=64), nullable=False),
            sa.Column("memory_type", sa.String(length=32), nullable=False),
            sa.Column("symbol", sa.String(length=16), nullable=True),
            sa.Column("timeframe", sa.String(length=10), nullable=True),
            sa.Column("correlation_id", sa.String(length=64), nullable=True),
            sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if not has_index("agent_memories", "ix_agent_memories_agent_id"):
        op.create_index(
            "ix_agent_memories_agent_id",
            "agent_memories",
            ["agent_id"],
            unique=False,
        )

    if not has_index("agent_memories", "idx_agent_memories_agent_type"):
        op.create_index(
            "idx_agent_memories_agent_type",
            "agent_memories",
            ["agent_id", "memory_type"],
            unique=False,
        )

    if not has_index("agent_memories", "idx_agent_memories_symbol"):
        op.create_index(
            "idx_agent_memories_symbol",
            "agent_memories",
            ["symbol"],
            unique=False,
        )

    if not has_index("agent_memories", "idx_agent_memories_correlation"):
        op.create_index(
            "idx_agent_memories_correlation",
            "agent_memories",
            ["correlation_id"],
            unique=False,
        )


def downgrade() -> None:
    if has_index("agent_memories", "idx_agent_memories_correlation"):
        op.drop_index("idx_agent_memories_correlation", table_name="agent_memories")
    if has_index("agent_memories", "idx_agent_memories_symbol"):
        op.drop_index("idx_agent_memories_symbol", table_name="agent_memories")
    if has_index("agent_memories", "idx_agent_memories_agent_type"):
        op.drop_index("idx_agent_memories_agent_type", table_name="agent_memories")
    if has_index("agent_memories", "ix_agent_memories_agent_id"):
        op.drop_index("ix_agent_memories_agent_id", table_name="agent_memories")
    if has_table("agent_memories"):
        op.drop_table("agent_memories")
