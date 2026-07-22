"""Add paper_positions table for persisted paper trades."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.database.migration_helpers import has_index, has_table

revision = "e1a2b3c4d5e6"
down_revision = "d9e3b2c4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not has_table("paper_positions"):
        op.create_table(
            "paper_positions",
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
            sa.Column("ticket", sa.Integer(), nullable=False),
            sa.Column("symbol", sa.String(length=16), nullable=False),
            sa.Column("signal", sa.String(length=16), nullable=False),
            sa.Column("entry", sa.Float(), nullable=False),
            sa.Column("stop_loss", sa.Float(), nullable=False),
            sa.Column("take_profit", sa.Float(), nullable=False),
            sa.Column("volume", sa.Float(), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("pnl", sa.Float(), nullable=False, server_default="0"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("ticket"),
        )

    if not has_index("paper_positions", "idx_paper_positions_ticket"):
        op.create_index(
            "idx_paper_positions_ticket",
            "paper_positions",
            ["ticket"],
            unique=True,
        )
    if not has_index("paper_positions", "idx_paper_positions_user_status"):
        op.create_index(
            "idx_paper_positions_user_status",
            "paper_positions",
            ["user_id", "status"],
            unique=False,
        )


def downgrade() -> None:
    if has_index("paper_positions", "idx_paper_positions_user_status"):
        op.drop_index("idx_paper_positions_user_status", table_name="paper_positions")
    if has_index("paper_positions", "idx_paper_positions_ticket"):
        op.drop_index("idx_paper_positions_ticket", table_name="paper_positions")
    if has_table("paper_positions"):
        op.drop_table("paper_positions")
