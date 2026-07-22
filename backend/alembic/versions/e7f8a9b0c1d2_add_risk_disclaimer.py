"""Add risk disclaimer acceptance fields to user_preferences."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.database.migration_helpers import has_column

revision = "e7f8a9b0c1d2"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not has_column("user_preferences", "risk_disclaimer_accepted"):
        op.add_column(
            "user_preferences",
            sa.Column(
                "risk_disclaimer_accepted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )

    if not has_column("user_preferences", "risk_disclaimer_accepted_at"):
        op.add_column(
            "user_preferences",
            sa.Column(
                "risk_disclaimer_accepted_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )

    if not has_column("user_preferences", "risk_disclaimer_version"):
        op.add_column(
            "user_preferences",
            sa.Column(
                "risk_disclaimer_version",
                sa.String(length=32),
                nullable=True,
            ),
        )

    if not has_column("user_preferences", "risk_disclaimer_app_version"):
        op.add_column(
            "user_preferences",
            sa.Column(
                "risk_disclaimer_app_version",
                sa.String(length=32),
                nullable=True,
            ),
        )


def downgrade() -> None:
    if has_column("user_preferences", "risk_disclaimer_app_version"):
        op.drop_column("user_preferences", "risk_disclaimer_app_version")
    if has_column("user_preferences", "risk_disclaimer_version"):
        op.drop_column("user_preferences", "risk_disclaimer_version")
    if has_column("user_preferences", "risk_disclaimer_accepted_at"):
        op.drop_column("user_preferences", "risk_disclaimer_accepted_at")
    if has_column("user_preferences", "risk_disclaimer_accepted"):
        op.drop_column("user_preferences", "risk_disclaimer_accepted")
