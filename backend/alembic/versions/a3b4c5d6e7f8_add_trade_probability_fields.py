"""Add trade probability and quality fields to recommendations."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.database.migration_helpers import has_column, has_index

revision = "a3b4c5d6e7f8"
down_revision = "f2b3c4d5e6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(
        postgresql.JSON(astext_type=sa.Text()),
        "postgresql",
    )

    if not has_column("recommendations", "trade_probability"):
        op.add_column(
            "recommendations",
            sa.Column(
                "trade_probability",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )
    if not has_column("recommendations", "similar_trade_count"):
        op.add_column(
            "recommendations",
            sa.Column(
                "similar_trade_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )
    if not has_column("recommendations", "historical_win_rate"):
        op.add_column(
            "recommendations",
            sa.Column(
                "historical_win_rate",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )
    if not has_column("recommendations", "expected_rr"):
        op.add_column(
            "recommendations",
            sa.Column(
                "expected_rr",
                sa.Numeric(precision=18, scale=8),
                nullable=False,
                server_default="0",
            ),
        )
    if not has_column("recommendations", "expected_hold_time"):
        op.add_column(
            "recommendations",
            sa.Column(
                "expected_hold_time",
                sa.String(length=64),
                nullable=False,
                server_default="",
            ),
        )
    if not has_column("recommendations", "trade_quality"):
        op.add_column(
            "recommendations",
            sa.Column(
                "trade_quality",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )
    if not has_column("recommendations", "quality_grade"):
        op.add_column(
            "recommendations",
            sa.Column(
                "quality_grade",
                sa.String(length=32),
                nullable=False,
                server_default="",
            ),
        )
    if not has_column("recommendations", "historical_insights"):
        op.add_column(
            "recommendations",
            sa.Column(
                "historical_insights",
                json_type,
                nullable=False,
                server_default=sa.text("'[]'"),
            ),
        )
    if not has_column("recommendations", "probability_detail"):
        op.add_column(
            "recommendations",
            sa.Column(
                "probability_detail",
                json_type,
                nullable=False,
                server_default=sa.text("'{}'"),
            ),
        )
    if not has_index("recommendations", "idx_recommendation_symbol_tf_signal_created"):
        op.create_index(
            "idx_recommendation_symbol_tf_signal_created",
            "recommendations",
            ["symbol", "timeframe", "signal", "created_at"],
        )


def downgrade() -> None:
    if has_index("recommendations", "idx_recommendation_symbol_tf_signal_created"):
        op.drop_index(
            "idx_recommendation_symbol_tf_signal_created",
            table_name="recommendations",
        )
    for name in (
        "probability_detail",
        "historical_insights",
        "quality_grade",
        "trade_quality",
        "expected_hold_time",
        "expected_rr",
        "historical_win_rate",
        "similar_trade_count",
        "trade_probability",
    ):
        if has_column("recommendations", name):
            op.drop_column("recommendations", name)
