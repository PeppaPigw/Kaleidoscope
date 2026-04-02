"""Add writing_documents table.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-02 16:58:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "writing_documents",
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
            server_default="Untitled",
        ),
        sa.Column(
            "markdown_content",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "plain_text_excerpt",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cover_image_url", sa.Text(), nullable=True),
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_writing_documents_deleted_at"),
        "writing_documents",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_writing_documents_user_id"),
        "writing_documents",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_writing_documents_updated_at",
        "writing_documents",
        ["updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_writing_documents_updated_at", table_name="writing_documents")
    op.drop_index(op.f("ix_writing_documents_user_id"), table_name="writing_documents")
    op.drop_index(
        op.f("ix_writing_documents_deleted_at"),
        table_name="writing_documents",
    )
    op.drop_table("writing_documents")
