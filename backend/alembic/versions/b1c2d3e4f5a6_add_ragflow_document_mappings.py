"""Add RAGFlow document mapping registry.

Revision ID: b1c2d3e4f5a6
Revises: d4e5f6a7b8c9
Create Date: 2026-03-31 23:35:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ragflow_document_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ragflow_dataset_id", sa.String(length=255), nullable=False),
        sa.Column("ragflow_document_id", sa.String(length=255), nullable=True),
        sa.Column("sync_hash", sa.String(length=64), nullable=True),
        sa.Column("parse_status", sa.String(length=20), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("paper_id", name="uq_ragflow_document_mappings_paper_id"),
        sa.UniqueConstraint(
            "collection_id",
            name="uq_ragflow_document_mappings_collection_id",
        ),
        sa.CheckConstraint(
            "(paper_id IS NOT NULL) != (collection_id IS NOT NULL)",
            name="ck_ragflow_exactly_one_scope",
        ),
    )


def downgrade() -> None:
    op.drop_table("ragflow_document_mappings")
