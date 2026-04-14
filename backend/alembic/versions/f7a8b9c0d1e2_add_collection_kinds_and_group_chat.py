"""Add typed collections, feed subscriptions, and collection chat.

Revision ID: f7a8b9c0d1e2
Revises: f6a7b8c9d0e1, e3f4a5b6c7d8
Create Date: 2026-04-05 23:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = ("f6a7b8c9d0e1", "e3f4a5b6c7d8")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "collections",
        sa.Column(
            "kind",
            sa.String(length=40),
            nullable=False,
            server_default="workspace",
        ),
    )
    op.add_column(
        "collections",
        sa.Column("parent_collection_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_collections_parent_collection_id",
        "collections",
        ["parent_collection_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_collections_parent_collection_id",
        "collections",
        "collections",
        ["parent_collection_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "collection_feed_subscriptions",
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feed_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["collections.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["feed_id"],
            ["rss_feeds.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "collection_id",
            "feed_id",
            name="uq_collection_feed_subscription",
        ),
    )
    op.create_index(
        "ix_collection_feed_subscriptions_collection_id",
        "collection_feed_subscriptions",
        ["collection_id"],
        unique=False,
    )
    op.create_index(
        "ix_collection_feed_subscriptions_feed_id",
        "collection_feed_subscriptions",
        ["feed_id"],
        unique=False,
    )
    op.create_index(
        "ix_collection_feed_subscriptions_deleted_at",
        "collection_feed_subscriptions",
        ["deleted_at"],
        unique=False,
    )

    op.create_table(
        "collection_chat_threads",
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default="00000000-0000-0000-0000-000000000001",
        ),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["collections.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_collection_chat_threads_collection_id",
        "collection_chat_threads",
        ["collection_id"],
        unique=False,
    )
    op.create_index(
        "ix_collection_chat_threads_user_id",
        "collection_chat_threads",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_collection_chat_threads_deleted_at",
        "collection_chat_threads",
        ["deleted_at"],
        unique=False,
    )

    op.create_table(
        "collection_chat_messages",
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default="00000000-0000-0000-0000-000000000001",
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["thread_id"],
            ["collection_chat_threads.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_collection_chat_messages_thread_id",
        "collection_chat_messages",
        ["thread_id"],
        unique=False,
    )
    op.create_index(
        "ix_collection_chat_messages_user_id",
        "collection_chat_messages",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_collection_chat_messages_deleted_at",
        "collection_chat_messages",
        ["deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_collection_chat_messages_deleted_at",
        table_name="collection_chat_messages",
    )
    op.drop_index(
        "ix_collection_chat_messages_user_id",
        table_name="collection_chat_messages",
    )
    op.drop_index(
        "ix_collection_chat_messages_thread_id",
        table_name="collection_chat_messages",
    )
    op.drop_table("collection_chat_messages")

    op.drop_index(
        "ix_collection_chat_threads_deleted_at",
        table_name="collection_chat_threads",
    )
    op.drop_index(
        "ix_collection_chat_threads_user_id",
        table_name="collection_chat_threads",
    )
    op.drop_index(
        "ix_collection_chat_threads_collection_id",
        table_name="collection_chat_threads",
    )
    op.drop_table("collection_chat_threads")

    op.drop_index(
        "ix_collection_feed_subscriptions_deleted_at",
        table_name="collection_feed_subscriptions",
    )
    op.drop_index(
        "ix_collection_feed_subscriptions_feed_id",
        table_name="collection_feed_subscriptions",
    )
    op.drop_index(
        "ix_collection_feed_subscriptions_collection_id",
        table_name="collection_feed_subscriptions",
    )
    op.drop_table("collection_feed_subscriptions")

    op.drop_constraint(
        "fk_collections_parent_collection_id",
        "collections",
        type_="foreignkey",
    )
    op.drop_index("ix_collections_parent_collection_id", table_name="collections")
    op.drop_column("collections", "parent_collection_id")
    op.drop_column("collections", "kind")
