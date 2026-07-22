"""Continuous learning system tables and outcome enrichment."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.database.migration_helpers import has_column, has_index, has_table

revision = "b4c5d6e7f8a9"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(
        postgresql.JSON(astext_type=sa.Text()),
        "postgresql",
    )

    skipped_tables: list[str] = []
    created_tables: list[str] = []

    # --- Enrich recommendation_outcomes ---
    for name, col in (
        ("result", sa.Column("result", sa.String(length=16), nullable=True)),
        ("entry", sa.Column("entry", sa.Float(), nullable=True)),
        ("sl", sa.Column("sl", sa.Float(), nullable=True)),
        ("tp", sa.Column("tp", sa.Float(), nullable=True)),
        ("rr", sa.Column("rr", sa.Float(), nullable=True)),
        ("profit", sa.Column("profit", sa.Float(), nullable=True)),
        ("duration_minutes", sa.Column("duration_minutes", sa.Integer(), nullable=True)),
        ("regime", sa.Column("regime", sa.String(length=32), nullable=True)),
        (
            "confidence_at_entry",
            sa.Column("confidence_at_entry", sa.Integer(), nullable=True),
        ),
    ):
        if not has_column("recommendation_outcomes", name):
            op.add_column("recommendation_outcomes", col)

    # --- Audit columns on recommendations ---
    for col, length, default in (
        ("engine_version", 32, "1.0.0"),
        ("learning_version", 32, "1.0.0"),
        ("weight_version", 64, "baseline"),
        ("indicator_version", 32, "1.0.0"),
        ("strategy_version", 32, "1.0.0"),
        ("market_regime", 32, None),
    ):
        if has_column("recommendations", col):
            continue
        if default is None:
            op.add_column(
                "recommendations",
                sa.Column(col, sa.String(length=length), nullable=True),
            )
        else:
            op.add_column(
                "recommendations",
                sa.Column(
                    col,
                    sa.String(length=length),
                    nullable=False,
                    server_default=default,
                ),
            )

    # --- paper_positions.recommendation_id ---
    if not has_column("paper_positions", "recommendation_id"):
        op.add_column(
            "paper_positions",
            sa.Column(
                "recommendation_id",
                sa.Integer(),
                sa.ForeignKey("recommendations.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
    if not has_index("paper_positions", "idx_paper_positions_recommendation"):
        op.create_index(
            "idx_paper_positions_recommendation",
            "paper_positions",
            ["recommendation_id"],
        )

    # --- New stats / version tables ---
    if not has_table("feature_statistics"):
        op.create_table(
            "feature_statistics",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
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
            sa.Column("feature_key", sa.String(length=64), nullable=False),
            sa.Column("symbol", sa.String(length=16), nullable=True),
            sa.Column("timeframe", sa.String(length=10), nullable=True),
            sa.Column("win_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("avg_rr", sa.Float(), nullable=False, server_default="0"),
            sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("profit_factor", sa.Float(), nullable=False, server_default="0"),
        )
        created_tables.append("feature_statistics")
    else:
        skipped_tables.append("feature_statistics")
    if not has_index("feature_statistics", "idx_feature_stats_key"):
        op.create_index("idx_feature_stats_key", "feature_statistics", ["feature_key"])

    if not has_table("symbol_statistics"):
        op.create_table(
            "symbol_statistics",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
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
            sa.Column("symbol", sa.String(length=16), nullable=False, unique=True),
            sa.Column("recommendations", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("win_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("avg_rr", sa.Float(), nullable=False, server_default="0"),
            sa.Column("avg_confidence", sa.Float(), nullable=False, server_default="0"),
            sa.Column("profit_factor", sa.Float(), nullable=False, server_default="0"),
        )
        created_tables.append("symbol_statistics")
    else:
        skipped_tables.append("symbol_statistics")

    if not has_table("timeframe_statistics"):
        op.create_table(
            "timeframe_statistics",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
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
            sa.Column("timeframe", sa.String(length=10), nullable=False, unique=True),
            sa.Column("win_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("avg_rr", sa.Float(), nullable=False, server_default="0"),
            sa.Column("trade_frequency", sa.Float(), nullable=False, server_default="0"),
            sa.Column("profit_factor", sa.Float(), nullable=False, server_default="0"),
            sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        )
        created_tables.append("timeframe_statistics")
    else:
        skipped_tables.append("timeframe_statistics")

    if not has_table("strategy_statistics"):
        op.create_table(
            "strategy_statistics",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
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
            sa.Column("combo_key", sa.String(length=128), nullable=False, unique=True),
            sa.Column("win_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("avg_rr", sa.Float(), nullable=False, server_default="0"),
            sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("profit_factor", sa.Float(), nullable=False, server_default="0"),
        )
        created_tables.append("strategy_statistics")
    else:
        skipped_tables.append("strategy_statistics")

    if not has_table("regime_statistics"):
        op.create_table(
            "regime_statistics",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
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
            sa.Column("regime", sa.String(length=32), nullable=False, unique=True),
            sa.Column("win_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("avg_rr", sa.Float(), nullable=False, server_default="0"),
            sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("profit_factor", sa.Float(), nullable=False, server_default="0"),
        )
        created_tables.append("regime_statistics")
    else:
        skipped_tables.append("regime_statistics")

    if not has_table("confidence_calibration"):
        op.create_table(
            "confidence_calibration",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
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
            sa.Column("bucket", sa.String(length=16), nullable=False, unique=True),
            sa.Column("predicted_mid", sa.Float(), nullable=False, server_default="0"),
            sa.Column("actual_win_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        )
        created_tables.append("confidence_calibration")
    else:
        skipped_tables.append("confidence_calibration")

    if not has_table("learning_versions"):
        op.create_table(
            "learning_versions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
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
            sa.Column("version", sa.String(length=64), nullable=False, unique=True),
            sa.Column("notes", sa.Text(), nullable=True),
        )
        created_tables.append("learning_versions")
    else:
        skipped_tables.append("learning_versions")

    if not has_table("weight_history"):
        op.create_table(
            "weight_history",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
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
            sa.Column("version", sa.String(length=64), nullable=False, unique=True),
            sa.Column("weights", json_type, nullable=False),
            sa.Column("learning_version", sa.String(length=64), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="0"),
        )
        created_tables.append("weight_history")
    else:
        skipped_tables.append("weight_history")
    if not has_index("weight_history", "idx_weight_history_active"):
        op.create_index("idx_weight_history_active", "weight_history", ["is_active"])


def downgrade() -> None:
    for table in (
        "weight_history",
        "learning_versions",
        "confidence_calibration",
        "regime_statistics",
        "strategy_statistics",
        "timeframe_statistics",
        "symbol_statistics",
        "feature_statistics",
    ):
        if has_table(table):
            op.drop_table(table)

    if has_index("paper_positions", "idx_paper_positions_recommendation"):
        op.drop_index("idx_paper_positions_recommendation", table_name="paper_positions")
    if has_column("paper_positions", "recommendation_id"):
        op.drop_column("paper_positions", "recommendation_id")

    for col in (
        "market_regime",
        "strategy_version",
        "indicator_version",
        "weight_version",
        "learning_version",
        "engine_version",
    ):
        if has_column("recommendations", col):
            op.drop_column("recommendations", col)

    for col in (
        "confidence_at_entry",
        "regime",
        "duration_minutes",
        "profit",
        "rr",
        "tp",
        "sl",
        "entry",
        "result",
    ):
        if has_column("recommendation_outcomes", col):
            op.drop_column("recommendation_outcomes", col)
