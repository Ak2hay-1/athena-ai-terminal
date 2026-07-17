"""Add institutional risk fields and NO_TRADE signal."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d9e3b2c4f5a6"
down_revision = "c8f2a1b3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("ALTER TYPE recommendation_signal ADD VALUE IF NOT EXISTS 'NO_TRADE'")
    else:
        # Non-Postgres: recreate check is handled by SQLAlchemy enums as strings in some setups.
        pass

    op.add_column(
        "recommendations",
        sa.Column(
            "entry_type",
            sa.String(length=16),
            nullable=False,
            server_default="NONE",
        ),
    )
    op.add_column(
        "recommendations",
        sa.Column(
            "risk_pips",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "recommendations",
        sa.Column(
            "reward_pips",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "recommendations",
        sa.Column(
            "sl_reason",
            sa.String(length=255),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "recommendations",
        sa.Column(
            "tp_reason",
            sa.String(length=255),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "recommendations",
        sa.Column(
            "validation",
            sa.JSON().with_variant(postgresql.JSON(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("recommendations", "validation")
    op.drop_column("recommendations", "tp_reason")
    op.drop_column("recommendations", "sl_reason")
    op.drop_column("recommendations", "reward_pips")
    op.drop_column("recommendations", "risk_pips")
    op.drop_column("recommendations", "entry_type")
    # Enum value NO_TRADE is left in place on PostgreSQL (cannot easily remove).
