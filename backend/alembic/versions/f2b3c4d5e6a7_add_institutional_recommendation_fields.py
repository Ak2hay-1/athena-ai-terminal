"""Add institutional recommendation enrichment JSON columns."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.database.migration_helpers import has_column

revision = "f2b3c4d5e6a7"
down_revision = "e1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(
        postgresql.JSON(astext_type=sa.Text()),
        "postgresql",
    )

    columns = (
        ("confidence_breakdown", "'{}'"),
        ("institutional_checklist", "'[]'"),
        ("market_heatmap", "'{}'"),
        ("entry_zone", "'{}'"),
    )
    for name, default in columns:
        if not has_column("recommendations", name):
            op.add_column(
                "recommendations",
                sa.Column(
                    name,
                    json_type,
                    nullable=False,
                    server_default=sa.text(default),
                ),
            )


def downgrade() -> None:
    for name in (
        "entry_zone",
        "market_heatmap",
        "institutional_checklist",
        "confidence_breakdown",
    ):
        if has_column("recommendations", name):
            op.drop_column("recommendations", name)
