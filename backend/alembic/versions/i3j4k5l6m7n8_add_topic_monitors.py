"""add topic monitors tables

Revision ID: i3j4k5l6m7n8
Revises: h2i3j4k5l6m7
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "i3j4k5l6m7n8"
down_revision = "h2i3j4k5l6m7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topic_monitors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dossier_id", UUID(as_uuid=True), sa.ForeignKey("research_dossiers.id"), nullable=False),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("query_config", JSONB, server_default="{}"),
        sa.Column("cadence", sa.String(20), server_default="daily"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_topic_monitors_dossier", "topic_monitors", ["dossier_id"])
    op.create_index("ix_topic_monitors_status", "topic_monitors", ["status"])

    op.create_table(
        "topic_monitor_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("monitor_id", UUID(as_uuid=True), sa.ForeignKey("topic_monitors.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("papers_checked", sa.Integer(), server_default="0"),
        sa.Column("papers_new", sa.Integer(), server_default="0"),
        sa.Column("claims_extracted", sa.Integer(), server_default="0"),
        sa.Column("ledger_mentions_added", sa.Integer(), server_default="0"),
        sa.Column("conflicts_found", sa.Integer(), server_default="0"),
        sa.Column("alerts_emitted", sa.Integer(), server_default="0"),
        sa.Column("summary", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_topic_monitor_runs_monitor", "topic_monitor_runs", ["monitor_id"])


def downgrade() -> None:
    op.drop_index("ix_topic_monitor_runs_monitor")
    op.drop_table("topic_monitor_runs")
    op.drop_index("ix_topic_monitors_status")
    op.drop_index("ix_topic_monitors_dossier")
    op.drop_table("topic_monitors")
