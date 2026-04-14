"""Add deep-analysis columns and governance support tables.

Revision ID: 08b6f9cddb0a
Revises: b1c2d3e4f5a6
Create Date: 2026-04-01 10:35:19.393971
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "08b6f9cddb0a"
down_revision: str | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.add_column(
        "papers",
        sa.Column("deep_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "papers",
        sa.Column("deep_analysis_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("diff", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)

    op.create_table(
        "webhooks",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("events", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("secret", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_webhooks_deleted_at"), "webhooks", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_webhooks_user_id"), "webhooks", ["user_id"], unique=False)

    op.create_table(
        "saved_searches",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(), server_default=DEFAULT_USER_ID, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("collection_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_saved_searches_collection_id"),
        "saved_searches",
        ["collection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_saved_searches_deleted_at"),
        "saved_searches",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_saved_searches_user_id"),
        "saved_searches",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "metadata_provenance",
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_metadata_provenance_paper_id"),
        "metadata_provenance",
        ["paper_id"],
        unique=False,
    )

    op.create_table(
        "reading_path_cache",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("from_paper_id", sa.UUID(), nullable=False),
        sa.Column("to_paper_id", sa.UUID(), nullable=False),
        sa.Column("path_paper_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["from_paper_id"], ["papers.id"]),
        sa.ForeignKeyConstraint(["to_paper_id"], ["papers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_reading_path_cache_from_paper_id"),
        "reading_path_cache",
        ["from_paper_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reading_path_cache_to_paper_id"),
        "reading_path_cache",
        ["to_paper_id"],
        unique=False,
    )

    op.create_table(
        "reproduction_attempts",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("code_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_reproduction_attempts_paper_id"),
        "reproduction_attempts",
        ["paper_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reproduction_attempts_user_id"),
        "reproduction_attempts",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "user_corrections",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("original_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("corrected_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_corrections_paper_id"),
        "user_corrections",
        ["paper_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_corrections_user_id"),
        "user_corrections",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "user_reading_status",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), server_default=DEFAULT_USER_ID, nullable=False),
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'unread'"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "paper_id", name="uq_user_paper_reading"),
    )
    op.create_index(
        op.f("ix_user_reading_status_paper_id"),
        "user_reading_status",
        ["paper_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_reading_status_user_id"),
        "user_reading_status",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_reading_status_user_id"), table_name="user_reading_status")
    op.drop_index(op.f("ix_user_reading_status_paper_id"), table_name="user_reading_status")
    op.drop_table("user_reading_status")

    op.drop_index(op.f("ix_user_corrections_user_id"), table_name="user_corrections")
    op.drop_index(op.f("ix_user_corrections_paper_id"), table_name="user_corrections")
    op.drop_table("user_corrections")

    op.drop_index(op.f("ix_reproduction_attempts_user_id"), table_name="reproduction_attempts")
    op.drop_index(op.f("ix_reproduction_attempts_paper_id"), table_name="reproduction_attempts")
    op.drop_table("reproduction_attempts")

    op.drop_index(op.f("ix_reading_path_cache_to_paper_id"), table_name="reading_path_cache")
    op.drop_index(op.f("ix_reading_path_cache_from_paper_id"), table_name="reading_path_cache")
    op.drop_table("reading_path_cache")

    op.drop_index(op.f("ix_metadata_provenance_paper_id"), table_name="metadata_provenance")
    op.drop_table("metadata_provenance")

    op.drop_index(op.f("ix_saved_searches_user_id"), table_name="saved_searches")
    op.drop_index(op.f("ix_saved_searches_deleted_at"), table_name="saved_searches")
    op.drop_index(op.f("ix_saved_searches_collection_id"), table_name="saved_searches")
    op.drop_table("saved_searches")

    op.drop_index(op.f("ix_webhooks_user_id"), table_name="webhooks")
    op.drop_index(op.f("ix_webhooks_deleted_at"), table_name="webhooks")
    op.drop_table("webhooks")

    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_column("papers", "deep_analysis_at")
    op.drop_column("papers", "deep_analysis")
