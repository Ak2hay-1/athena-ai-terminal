"""Add journal_entries table for persisted trading journal."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.database.migration_helpers import has_index
from app.database.migration_helpers import has_table

revision = "f8a9b0c1d2e3"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not has_table("journal_entries"):
        op.create_table(
            "journal_entries",
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
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("entry_type", sa.String(length=32), nullable=False),
            sa.Column("recommendation_id", sa.Integer(), nullable=True),
            sa.Column("paper_position_id", sa.Integer(), nullable=True),
            sa.Column("symbol", sa.String(length=16), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column(
                "tags",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["recommendation_id"],
                ["recommendations.id"],
                ondelete="SET NULL",
            ),
            sa.ForeignKeyConstraint(
                ["paper_position_id"],
                ["paper_positions.id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if not has_index("journal_entries", "idx_journal_entries_user_created"):
        op.create_index(
            "idx_journal_entries_user_created",
            "journal_entries",
            ["user_id", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    if has_index("journal_entries", "idx_journal_entries_user_created"):
        op.drop_index(
            "idx_journal_entries_user_created",
            table_name="journal_entries",
        )
    if has_table("journal_entries"):
        op.drop_table("journal_entries")
