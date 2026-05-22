"""add global claim ledger tables

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "h2i3j4k5l6m7"
down_revision = "g1h2i3j4k5l6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "global_claims",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("canonical_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("claim_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("claim_type", sa.String(30), nullable=True),
        sa.Column("topic_terms", JSONB, server_default="[]"),
        sa.Column("entities", JSONB, server_default="{}"),
        sa.Column("qualifiers", JSONB, server_default="{}"),
        sa.Column("first_seen_dossier_id", UUID(as_uuid=True), sa.ForeignKey("research_dossiers.id"), nullable=True),
        sa.Column("first_seen_paper_id", UUID(as_uuid=True), sa.ForeignKey("papers.id"), nullable=True),
        sa.Column("support_count", sa.Integer(), server_default="0"),
        sa.Column("contradict_count", sa.Integer(), server_default="0"),
        sa.Column("qualify_count", sa.Integer(), server_default="0"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_global_claims_status", "global_claims", ["status"])
    op.create_index("ix_global_claims_topic_terms", "global_claims", ["topic_terms"], postgresql_using="gin")
    op.create_index("ix_global_claims_deleted_at", "global_claims", ["deleted_at"])

    op.create_table(
        "claim_mentions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("global_claim_id", UUID(as_uuid=True), sa.ForeignKey("global_claims.id"), nullable=False),
        sa.Column("dossier_id", UUID(as_uuid=True), sa.ForeignKey("research_dossiers.id"), nullable=True),
        sa.Column("paper_id", UUID(as_uuid=True), sa.ForeignKey("papers.id"), nullable=True),
        sa.Column("source_tool", sa.String(50), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("stance", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("verdict", sa.String(20), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("evidence", JSONB, server_default="[]"),
        sa.Column("metadata_json", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_claim_mentions_global", "claim_mentions", ["global_claim_id"])
    op.create_index("ix_claim_mentions_dossier", "claim_mentions", ["dossier_id"])
    op.create_index("ix_claim_mentions_paper", "claim_mentions", ["paper_id"])

    op.create_table(
        "claim_relations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_claim_id", UUID(as_uuid=True), sa.ForeignKey("global_claims.id"), nullable=False),
        sa.Column("target_claim_id", UUID(as_uuid=True), sa.ForeignKey("global_claims.id"), nullable=False),
        sa.Column("relation", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("evidence", JSONB, server_default="[]"),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("source_claim_id", "target_claim_id", "relation"),
    )
    op.create_index("ix_claim_relations_source", "claim_relations", ["source_claim_id"])
    op.create_index("ix_claim_relations_target", "claim_relations", ["target_claim_id"])


def downgrade() -> None:
    op.drop_index("ix_claim_relations_target")
    op.drop_index("ix_claim_relations_source")
    op.drop_table("claim_relations")
    op.drop_index("ix_claim_mentions_paper")
    op.drop_index("ix_claim_mentions_dossier")
    op.drop_index("ix_claim_mentions_global")
    op.drop_table("claim_mentions")
    op.drop_index("ix_global_claims_deleted_at")
    op.drop_index("ix_global_claims_topic_terms")
    op.drop_index("ix_global_claims_status")
    op.drop_table("global_claims")
