"""Add markdown content columns to papers

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-23 13:00:00.000000

Adds:
- papers.full_text_markdown (Text) — primary content storage
- papers.markdown_provenance (JSONB) — extraction metadata
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('papers', sa.Column(
        'full_text_markdown', sa.Text(), nullable=True
    ))
    op.add_column('papers', sa.Column(
        'markdown_provenance',
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    ))


def downgrade() -> None:
    op.drop_column('papers', 'markdown_provenance')
    op.drop_column('papers', 'full_text_markdown')
