"""Add auto-trade preference fields to user_preferences."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.database.migration_helpers import has_column

revision = "g1h2i3j4k5l6"
down_revision = "f8a9b0c1d2e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not has_column("user_preferences", "auto_trade_enabled"):
        op.add_column(
            "user_preferences",
            sa.Column(
                "auto_trade_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )

    if not has_column("user_preferences", "auto_trade_symbols"):
        op.add_column(
            "user_preferences",
            sa.Column(
                "auto_trade_symbols",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
        )

    if not has_column("user_preferences", "auto_trade_timeframes"):
        op.add_column(
            "user_preferences",
            sa.Column(
                "auto_trade_timeframes",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
        )

    if not has_column("user_preferences", "auto_trade_min_confidence"):
        op.add_column(
            "user_preferences",
            sa.Column(
                "auto_trade_min_confidence",
                sa.Integer(),
                nullable=False,
                server_default="70",
            ),
        )

    if not has_column("user_preferences", "auto_trade_min_confluence"):
        op.add_column(
            "user_preferences",
            sa.Column(
                "auto_trade_min_confluence",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )

    if not has_column("user_preferences", "auto_trade_min_rr"):
        op.add_column(
            "user_preferences",
            sa.Column(
                "auto_trade_min_rr",
                sa.Float(),
                nullable=False,
                server_default="0",
            ),
        )

    if not has_column("user_preferences", "auto_trade_volume"):
        op.add_column(
            "user_preferences",
            sa.Column(
                "auto_trade_volume",
                sa.Float(),
                nullable=False,
                server_default="0.01",
            ),
        )


def downgrade() -> None:
    for column in (
        "auto_trade_volume",
        "auto_trade_min_rr",
        "auto_trade_min_confluence",
        "auto_trade_min_confidence",
        "auto_trade_timeframes",
        "auto_trade_symbols",
        "auto_trade_enabled",
    ):
        if has_column("user_preferences", column):
            op.drop_column("user_preferences", column)
