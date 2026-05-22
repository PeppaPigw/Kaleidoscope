"""Add research runs tables for autonomous execution engine.

Revision ID: l6m7n8o9p0q1
Revises: k5l6m7n8o9p0
Create Date: 2025-05-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "l6m7n8o9p0q1"
down_revision = "k5l6m7n8o9p0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dossier_id", UUID(as_uuid=True), sa.ForeignKey("research_dossiers.id"), nullable=False, index=True),
        sa.Column("objective", sa.String(50), nullable=False, server_default="maximize_certainty"),
        sa.Column("status", sa.String(20), nullable=False, server_default="running", index=True),
        sa.Column("budget_papers", sa.Integer, server_default="10"),
        sa.Column("max_steps", sa.Integer, server_default="20"),
        sa.Column("target_confidence", sa.Float, nullable=True),
        sa.Column("target_claims", JSONB, nullable=True),
        sa.Column("allowed_actions", JSONB, nullable=True),
        sa.Column("papers_used", sa.Integer, server_default="0"),
        sa.Column("steps_completed", sa.Integer, server_default="0"),
        sa.Column("claims_added", sa.Integer, server_default="0"),
        sa.Column("claims_updated", sa.Integer, server_default="0"),
        sa.Column("contradictions_resolved", sa.Integer, server_default="0"),
        sa.Column("net_confidence_delta", sa.Float, server_default="0.0"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stop_reason", sa.String(100), nullable=True),
        sa.Column("summary", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, index=True),
    )

    op.create_table(
        "research_run_steps",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("research_runs.id"), nullable=False, index=True),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("target_claim_id", UUID(as_uuid=True), nullable=True),
        sa.Column("target_claim_text", sa.Text, nullable=True),
        sa.Column("predicted_utility", sa.Float, server_default="0.0"),
        sa.Column("predicted_lift", sa.Float, server_default="0.0"),
        sa.Column("actual_lift", sa.Float, nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("tool_calls", JSONB, nullable=True),
        sa.Column("tool_results", JSONB, nullable=True),
        sa.Column("claims_produced", JSONB, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, index=True),
    )

    op.create_index("ix_research_run_steps_run_step", "research_run_steps", ["run_id", "step_number"])


def downgrade() -> None:
    op.drop_index("ix_research_run_steps_run_step", table_name="research_run_steps")
    op.drop_table("research_run_steps")
    op.drop_table("research_runs")
