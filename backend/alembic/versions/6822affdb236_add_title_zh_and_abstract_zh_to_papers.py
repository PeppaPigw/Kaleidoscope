"""add_title_zh_and_abstract_zh_to_papers

Revision ID: 6822affdb236
Revises: 0f9e8d7c6b5a
Create Date: 2026-04-14 16:14:42.086672

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6822affdb236'
down_revision: Union[str, None] = '0f9e8d7c6b5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Chinese translation fields for title and abstract
    op.add_column('papers', sa.Column('title_zh', sa.Text(), nullable=True))
    op.add_column('papers', sa.Column('abstract_zh', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove Chinese translation fields
    op.drop_column('papers', 'abstract_zh')
    op.drop_column('papers', 'title_zh')
