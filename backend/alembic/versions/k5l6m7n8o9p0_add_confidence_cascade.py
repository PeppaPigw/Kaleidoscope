"""add confidence cascade columns

Revision ID: k5l6m7n8o9p0
Revises: j4k5l6m7n8o9
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "k5l6m7n8o9p0"
down_revision = "j4k5l6m7n8o9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("global_claims", sa.Column("direct_confidence", sa.Float(), nullable=True))
    op.add_column("global_claims", sa.Column("effective_confidence", sa.Float(), nullable=True))
    op.add_column("global_claims", sa.Column("cascade_depth", sa.Integer(), server_default="0"))

    op.create_table(
        "claim_confidence_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("claim_id", UUID(as_uuid=True), sa.ForeignKey("global_claims.id"), nullable=False),
        sa.Column("trigger_claim_id", UUID(as_uuid=True), sa.ForeignKey("global_claims.id"), nullable=True),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("before_confidence", sa.Float(), nullable=True),
        sa.Column("after_confidence", sa.Float(), nullable=True),
        sa.Column("delta", sa.Float(), nullable=True),
        sa.Column("depth", sa.Integer(), server_default="0"),
        sa.Column("path", JSONB, server_default="[]"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_confidence_events_claim", "claim_confidence_events", ["claim_id"])
    op.create_index("ix_confidence_events_trigger", "claim_confidence_events", ["trigger_claim_id"])


def downgrade() -> None:
    op.drop_index("ix_confidence_events_trigger")
    op.drop_index("ix_confidence_events_claim")
    op.drop_table("claim_confidence_events")
    op.drop_column("global_claims", "cascade_depth")
    op.drop_column("global_claims", "effective_confidence")
    op.drop_column("global_claims", "direct_confidence")
