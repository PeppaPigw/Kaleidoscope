"""add research dossiers table

Revision ID: g1h2i3j4k5l6
Revises: f7a8b9c0d1e2
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "g1h2i3j4k5l6"
down_revision = "a0b1c2d3e4f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_dossiers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("research_question", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_by", sa.String(128), nullable=True),
        sa.Column("papers_seen", JSONB, server_default="{}"),
        sa.Column("papers_excluded", JSONB, server_default="{}"),
        sa.Column("claims", JSONB, server_default="{}"),
        sa.Column("evidence", JSONB, server_default="{}"),
        sa.Column("gaps", JSONB, server_default="{}"),
        sa.Column("decisions", JSONB, server_default="{}"),
        sa.Column("open_questions", JSONB, server_default="[]"),
        sa.Column("failed_searches", JSONB, server_default="[]"),
        sa.Column("next_actions", JSONB, server_default="[]"),
        sa.Column("coverage_score", sa.Integer(), nullable=True),
        sa.Column("confidence_summary", JSONB, server_default="{}"),
        sa.Column("memory_log", JSONB, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_research_dossiers_topic", "research_dossiers", ["topic"])
    op.create_index("ix_research_dossiers_status", "research_dossiers", ["status"])
    op.create_index("ix_research_dossiers_deleted_at", "research_dossiers", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_research_dossiers_deleted_at")
    op.drop_index("ix_research_dossiers_status")
    op.drop_index("ix_research_dossiers_topic")
    op.drop_table("research_dossiers")
