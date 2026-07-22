"""Market data engine: market_ticks + indicator_values (+ optional TimescaleDB)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "h2i3j4k5l6m7"
down_revision = "g1h2i3j4k5l6"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_table(name)


def upgrade() -> None:
    if not _has_table("market_ticks"):
        op.create_table(
            "market_ticks",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("symbol", sa.String(length=20), nullable=False),
            sa.Column("time", sa.DateTime(timezone=True), nullable=False),
            sa.Column("time_msc", sa.BigInteger(), nullable=False),
            sa.Column("bid", sa.Float(), nullable=False, server_default="0"),
            sa.Column("ask", sa.Float(), nullable=False, server_default="0"),
            sa.Column("last", sa.Float(), nullable=False, server_default="0"),
            sa.Column(
                "spread", sa.Float(), nullable=False, server_default="0"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("symbol", "time_msc", name="uq_market_tick"),
        )
        op.create_index(
            "idx_market_tick_symbol_time",
            "market_ticks",
            ["symbol", "time"],
        )
        op.create_index(
            op.f("ix_market_ticks_symbol"),
            "market_ticks",
            ["symbol"],
        )

    if not _has_table("indicator_values"):
        op.create_table(
            "indicator_values",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("symbol", sa.String(length=20), nullable=False),
            sa.Column("timeframe", sa.String(length=10), nullable=False),
            sa.Column("time", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "values",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "indicator_version",
                sa.String(length=20),
                nullable=False,
                server_default="1.0.0",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "symbol", "timeframe", "time", name="uq_indicator_value"
            ),
        )
        op.create_index(
            "idx_indicator_symbol_tf_time",
            "indicator_values",
            ["symbol", "timeframe", "time"],
        )
        op.create_index(
            op.f("ix_indicator_values_symbol"),
            "indicator_values",
            ["symbol"],
        )
        op.create_index(
            op.f("ix_indicator_values_timeframe"),
            "indicator_values",
            ["timeframe"],
        )

    # Optional TimescaleDB acceleration — best effort on a separate
    # autocommit connection so failures cannot poison this migration.
    # Plain PostgreSQL remains fully supported without the extension.
    try:
        engine = op.get_bind().engine
        with engine.connect() as conn:
            conn = conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(
                sa.text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
            )
    except Exception:
        # No extension / insufficient privileges — standard PostgreSQL
        # indexes are sufficient.
        pass


def downgrade() -> None:
    if _has_table("indicator_values"):
        op.drop_table("indicator_values")
    if _has_table("market_ticks"):
        op.drop_table("market_ticks")
