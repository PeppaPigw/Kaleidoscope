"""add_overview_image_to_papers

Revision ID: a9b0c1d2e3f4
Revises: 08b6f9cddb0a
Create Date: 2026-04-03 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a9b0c1d2e3f4"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "papers",
        sa.Column(
            "overview_image",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "papers",
        sa.Column("overview_image_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("papers", "overview_image_at")
    op.drop_column("papers", "overview_image")
