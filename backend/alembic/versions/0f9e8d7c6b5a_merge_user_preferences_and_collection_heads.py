"""Merge user preferences and collection chat heads.

Revision ID: 0f9e8d7c6b5a
Revises: a3b4c5d6e7f8, f7a8b9c0d1e2
Create Date: 2026-04-14 14:30:00.000000
"""

from collections.abc import Sequence

revision: str = "0f9e8d7c6b5a"
down_revision: str | Sequence[str] | None = ("a3b4c5d6e7f8", "f7a8b9c0d1e2")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
