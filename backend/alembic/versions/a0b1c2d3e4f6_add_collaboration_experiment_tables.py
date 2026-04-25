"""Add collaboration and experiment runtime tables.

Revision ID: a0b1c2d3e4f6
Revises: 9a0b1c2d3e4f
Create Date: 2026-04-25 21:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a0b1c2d3e4f6"
down_revision: str | Sequence[str] | None = "9a0b1c2d3e4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "paper_comments",
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("anchor_type", sa.String(length=50), nullable=True),
        sa.Column("anchor_ref", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["paper_comments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_paper_comments_paper_id"),
        "paper_comments",
        ["paper_id"],
        unique=False,
    )
    op.create_index(op.f("ix_paper_comments_user_id"), "paper_comments", ["user_id"], unique=False)

    op.create_table(
        "review_tasks",
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("assignee_id", sa.UUID(), nullable=False),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("decision", sa.String(length=30), nullable=True),
        sa.Column("decision_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_review_tasks_assignee_id"),
        "review_tasks",
        ["assignee_id"],
        unique=False,
    )
    op.create_index(op.f("ix_review_tasks_paper_id"), "review_tasks", ["paper_id"], unique=False)

    op.create_table(
        "screening_decisions",
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("reviewer_id", sa.UUID(), nullable=False),
        sa.Column("stage", sa.String(length=30), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("criteria_met", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_screening_decisions_paper_id"),
        "screening_decisions",
        ["paper_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_screening_decisions_reviewer_id"),
        "screening_decisions",
        ["reviewer_id"],
        unique=False,
    )

    op.create_table(
        "experiments",
        sa.Column("paper_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("setup", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_experiments_paper_id"), "experiments", ["paper_id"], unique=False)

    op.create_table(
        "methods",
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("typical_params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("paper_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "datasets",
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("domain", sa.String(length=100), nullable=True),
        sa.Column("size_description", sa.String(length=255), nullable=True),
        sa.Column("license", sa.String(length=100), nullable=True),
        sa.Column("metadata_extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("paper_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("datasets")
    op.drop_table("methods")
    op.drop_index(op.f("ix_experiments_paper_id"), table_name="experiments")
    op.drop_table("experiments")
    op.drop_index(op.f("ix_screening_decisions_reviewer_id"), table_name="screening_decisions")
    op.drop_index(op.f("ix_screening_decisions_paper_id"), table_name="screening_decisions")
    op.drop_table("screening_decisions")
    op.drop_index(op.f("ix_review_tasks_paper_id"), table_name="review_tasks")
    op.drop_index(op.f("ix_review_tasks_assignee_id"), table_name="review_tasks")
    op.drop_table("review_tasks")
    op.drop_index(op.f("ix_paper_comments_user_id"), table_name="paper_comments")
    op.drop_index(op.f("ix_paper_comments_paper_id"), table_name="paper_comments")
    op.drop_table("paper_comments")
