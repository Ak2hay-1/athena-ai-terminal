"""Add institutional qualification / lifecycle fields to recommendations."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.database.migration_helpers import has_column
from app.database.migration_helpers import has_index

revision = "i3j4k5l6m7n8"
down_revision = "h2i3j4k5l6m7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(
        postgresql.JSON(astext_type=sa.Text()),
        "postgresql",
    )

    cols = [
        ("setup_quality", sa.Column("setup_quality", sa.Integer(), nullable=False, server_default="0")),
        ("setup_quality_grade", sa.Column("setup_quality_grade", sa.String(32), nullable=False, server_default="")),
        (
            "setup_quality_components",
            sa.Column("setup_quality_components", json_type, nullable=False, server_default="{}"),
        ),
        ("scanner_group", sa.Column("scanner_group", sa.String(32), nullable=False, server_default="no_trade")),
        ("lifecycle_state", sa.Column("lifecycle_state", sa.String(32), nullable=False, server_default="NEW")),
        (
            "rejection_checklist",
            sa.Column("rejection_checklist", json_type, nullable=False, server_default="[]"),
        ),
        ("qualification_score", sa.Column("qualification_score", sa.Integer(), nullable=False, server_default="0")),
        ("trend_strength", sa.Column("trend_strength", sa.Float(), nullable=False, server_default="0")),
        (
            "correlated",
            sa.Column("correlated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        ),
        ("correlation_note", sa.Column("correlation_note", sa.String(255), nullable=False, server_default="")),
        ("parent_recommendation_id", sa.Column("parent_recommendation_id", sa.Integer(), nullable=True)),
    ]

    for name, column in cols:
        if not has_column("recommendations", name):
            op.add_column("recommendations", column)

    if not has_index("recommendations", "ix_recommendations_lifecycle_state"):
        op.create_index(
            "ix_recommendations_lifecycle_state",
            "recommendations",
            ["lifecycle_state"],
        )


def downgrade() -> None:
    if has_index("recommendations", "ix_recommendations_lifecycle_state"):
        op.drop_index("ix_recommendations_lifecycle_state", table_name="recommendations")

    for name in (
        "parent_recommendation_id",
        "correlation_note",
        "correlated",
        "trend_strength",
        "qualification_score",
        "rejection_checklist",
        "lifecycle_state",
        "scanner_group",
        "setup_quality_components",
        "setup_quality_grade",
        "setup_quality",
    ):
        if has_column("recommendations", name):
            op.drop_column("recommendations", name)
