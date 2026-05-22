"""add evidence strength scoring columns

Revision ID: j4k5l6m7n8o9
Revises: i3j4k5l6m7n8
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "j4k5l6m7n8o9"
down_revision = "i3j4k5l6m7n8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("global_claims", sa.Column("evidence_strength_score", sa.Float(), nullable=True))
    op.add_column("global_claims", sa.Column("weighted_support", sa.Float(), nullable=True))
    op.add_column("global_claims", sa.Column("weighted_contradict", sa.Float(), nullable=True))
    op.add_column("global_claims", sa.Column("replication_score", sa.Float(), nullable=True))
    op.add_column("global_claims", sa.Column("strength_breakdown", JSONB, server_default="{}"))

    op.add_column("claim_mentions", sa.Column("strength_score", sa.Float(), nullable=True))
    op.add_column("claim_mentions", sa.Column("strength_breakdown", JSONB, server_default="{}"))


def downgrade() -> None:
    op.drop_column("claim_mentions", "strength_breakdown")
    op.drop_column("claim_mentions", "strength_score")
    op.drop_column("global_claims", "strength_breakdown")
    op.drop_column("global_claims", "replication_score")
    op.drop_column("global_claims", "weighted_contradict")
    op.drop_column("global_claims", "weighted_support")
    op.drop_column("global_claims", "evidence_strength_score")
