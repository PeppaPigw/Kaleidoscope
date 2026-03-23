"""P1 + P2 schema additions

Revision ID: a1b2c3d4e5f6
Revises: 625357ed3fc8
Create Date: 2026-03-21 20:30:00.000000

P1 additions:
- collections, collection_papers, tags, paper_tags, user_reading_statuses tables
- papers.reading_status column

P2 additions:
- papers: visibility, source_type, local_annotations, parsed_sections, parsed_figures
- topics, paper_topics tables
- alert_rules, alerts, digests tables
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '625357ed3fc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════
    # P1: Collections, Tags, Reading Status
    # ═══════════════════════════════════════════════════════════════

    op.create_table('collections',
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('collection_type', sa.String(length=20), nullable=False),
        sa.Column('filter_query', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_collections_deleted_at'), 'collections', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_collections_user_id'), 'collections', ['user_id'], unique=False)

    op.create_table('collection_papers',
        sa.Column('collection_id', sa.UUID(), nullable=False),
        sa.Column('paper_id', sa.UUID(), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id']),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('collection_id', 'paper_id')
    )

    op.create_table('tags',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tags_deleted_at'), 'tags', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_tags_user_id'), 'tags', ['user_id'], unique=False)

    op.create_table('paper_tags',
        sa.Column('paper_id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('user_reading_statuses',
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('paper_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_reading_statuses_user_id'), 'user_reading_statuses', ['user_id'], unique=False)
    op.create_index('ix_urs_user_paper', 'user_reading_statuses', ['user_id', 'paper_id'], unique=True)

    # P1: Add reading_status to papers
    op.add_column('papers',
        sa.Column('reading_status', sa.String(length=20), nullable=False, server_default='unread')
    )

    # ═══════════════════════════════════════════════════════════════
    # P2: Papers extended columns
    # ═══════════════════════════════════════════════════════════════

    op.add_column('papers',
        sa.Column('visibility', sa.String(length=20), nullable=False, server_default='private')
    )
    op.add_column('papers',
        sa.Column('source_type', sa.String(length=20), nullable=False, server_default='remote')
    )
    op.add_column('papers',
        sa.Column('local_annotations', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column('papers',
        sa.Column('parsed_sections', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column('papers',
        sa.Column('parsed_figures', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )

    # ═══════════════════════════════════════════════════════════════
    # P2: Topics
    # ═══════════════════════════════════════════════════════════════

    op.create_table('topics',
        sa.Column('label', sa.Text(), nullable=False),
        sa.Column('keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('representative_docs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('paper_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('trend_direction', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('paper_topics',
        sa.Column('paper_id', sa.UUID(), nullable=False),
        sa.Column('topic_id', sa.UUID(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_paper_topics_paper_id'), 'paper_topics', ['paper_id'], unique=False)
    op.create_index(op.f('ix_paper_topics_topic_id'), 'paper_topics', ['topic_id'], unique=False)

    # ═══════════════════════════════════════════════════════════════
    # P2: Alerts & Monitoring
    # ═══════════════════════════════════════════════════════════════

    op.create_table('alert_rules',
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('rule_type', sa.String(length=30), nullable=False),
        sa.Column('condition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('actions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trigger_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alert_rules_user_id'), 'alert_rules', ['user_id'], unique=False)

    op.create_table('alerts',
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('rule_id', sa.UUID(), nullable=True),
        sa.Column('alert_type', sa.String(length=30), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('paper_id', sa.UUID(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.ForeignKeyConstraint(['rule_id'], ['alert_rules.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_user_id'), 'alerts', ['user_id'], unique=False)

    op.create_table('digests',
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('period', sa.String(length=10), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('paper_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('paper_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_digests_user_id'), 'digests', ['user_id'], unique=False)


def downgrade() -> None:
    # P2: Alerts
    op.drop_index(op.f('ix_digests_user_id'), table_name='digests')
    op.drop_table('digests')
    op.drop_index(op.f('ix_alerts_user_id'), table_name='alerts')
    op.drop_table('alerts')
    op.drop_index(op.f('ix_alert_rules_user_id'), table_name='alert_rules')
    op.drop_table('alert_rules')

    # P2: Topics
    op.drop_index(op.f('ix_paper_topics_topic_id'), table_name='paper_topics')
    op.drop_index(op.f('ix_paper_topics_paper_id'), table_name='paper_topics')
    op.drop_table('paper_topics')
    op.drop_table('topics')

    # P2: Papers extended columns
    op.drop_column('papers', 'parsed_figures')
    op.drop_column('papers', 'parsed_sections')
    op.drop_column('papers', 'local_annotations')
    op.drop_column('papers', 'source_type')
    op.drop_column('papers', 'visibility')

    # P1: Reading status
    op.drop_column('papers', 'reading_status')

    # P1: Collections, Tags
    op.drop_index('ix_urs_user_paper', table_name='user_reading_statuses')
    op.drop_index(op.f('ix_user_reading_statuses_user_id'), table_name='user_reading_statuses')
    op.drop_table('user_reading_statuses')
    op.drop_table('paper_tags')
    op.drop_index(op.f('ix_tags_user_id'), table_name='tags')
    op.drop_index(op.f('ix_tags_deleted_at'), table_name='tags')
    op.drop_table('tags')
    op.drop_table('collection_papers')
    op.drop_index(op.f('ix_collections_user_id'), table_name='collections')
    op.drop_index(op.f('ix_collections_deleted_at'), table_name='collections')
    op.drop_table('collections')
