"""add_deep_analysis_zh_to_papers

Revision ID: b0c1d2e3f4a5
Revises: a9b0c1d2e3f4
Create Date: 2026-04-03 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b0c1d2e3f4a5"
down_revision: Union[str, None] = "a9b0c1d2e3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "papers",
        sa.Column("deep_analysis_zh", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "papers",
        sa.Column(
            "deep_analysis_zh_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("papers", "deep_analysis_zh_at")
    op.drop_column("papers", "deep_analysis_zh")
