"""Phase 5: user preferences and notification tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.database.migration_helpers import has_index
from app.database.migration_helpers import has_table

revision = "d6e7f8a9b0c1"
down_revision = "c5d6e7f8a9b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not has_table("user_preferences"):
        op.create_table(
            "user_preferences",
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
            sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
            sa.Column("language", sa.String(length=16), nullable=False, server_default="en"),
            sa.Column(
                "trading_style",
                sa.String(length=32),
                nullable=False,
                server_default="intraday",
            ),
            sa.Column(
                "risk_profile",
                sa.String(length=32),
                nullable=False,
                server_default="balanced",
            ),
            sa.Column(
                "preferred_channel",
                sa.String(length=32),
                nullable=False,
                server_default="websocket",
            ),
            sa.Column(
                "notification_frequency",
                sa.String(length=32),
                nullable=False,
                server_default="normal",
            ),
            sa.Column(
                "quiet_hours_start",
                sa.String(length=8),
                nullable=False,
                server_default="22:00",
            ),
            sa.Column(
                "quiet_hours_end",
                sa.String(length=8),
                nullable=False,
                server_default="07:00",
            ),
            sa.Column("preferred_sessions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column(
                "preferred_timeframes",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column(
                "preferred_strategies",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column("ignored_symbols", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("favorite_assets", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("preferred_rr", sa.Float(), nullable=True),
            sa.Column("soft_weights", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("telegram_chat_id", sa.String(length=64), nullable=True),
            sa.Column("discord_webhook_url", sa.String(length=512), nullable=True),
            sa.Column("email_override", sa.String(length=255), nullable=True),
            sa.Column("push_device_token", sa.String(length=512), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", name="uq_user_preferences_user"),
        )

    if not has_table("notification_deliveries"):
        op.create_table(
            "notification_deliveries",
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
            sa.Column("channel", sa.String(length=32), nullable=False),
            sa.Column("message_type", sa.String(length=64), nullable=False),
            sa.Column("priority", sa.String(length=16), nullable=False, server_default="Medium"),
            sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="queued"),
            sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("latency_ms", sa.Float(), nullable=True),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("dedupe_key", sa.String(length=128), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not has_index("notification_deliveries", "idx_notification_deliveries_user"):
        op.create_index(
            "idx_notification_deliveries_user",
            "notification_deliveries",
            ["user_id"],
            unique=False,
        )
    if not has_index("notification_deliveries", "idx_notification_deliveries_dedupe"):
        op.create_index(
            "idx_notification_deliveries_dedupe",
            "notification_deliveries",
            ["dedupe_key"],
            unique=False,
        )
    if not has_index("notification_deliveries", "idx_notification_deliveries_status"):
        op.create_index(
            "idx_notification_deliveries_status",
            "notification_deliveries",
            ["status"],
            unique=False,
        )

    if not has_table("notification_interactions"):
        op.create_table(
            "notification_interactions",
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
            sa.Column("delivery_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("action", sa.String(length=16), nullable=False),
            sa.ForeignKeyConstraint(
                ["delivery_id"],
                ["notification_deliveries.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not has_index("notification_interactions", "idx_notification_interactions_delivery"):
        op.create_index(
            "idx_notification_interactions_delivery",
            "notification_interactions",
            ["delivery_id"],
            unique=False,
        )


def downgrade() -> None:
    if has_index("notification_interactions", "idx_notification_interactions_delivery"):
        op.drop_index(
            "idx_notification_interactions_delivery",
            table_name="notification_interactions",
        )
    if has_table("notification_interactions"):
        op.drop_table("notification_interactions")

    for idx in (
        "idx_notification_deliveries_status",
        "idx_notification_deliveries_dedupe",
        "idx_notification_deliveries_user",
    ):
        if has_index("notification_deliveries", idx):
            op.drop_index(idx, table_name="notification_deliveries")
    if has_table("notification_deliveries"):
        op.drop_table("notification_deliveries")

    if has_table("user_preferences"):
        op.drop_table("user_preferences")
