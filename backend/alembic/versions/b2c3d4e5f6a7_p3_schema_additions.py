"""P3 schema: claims, evidence, personal knowledge

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-21 21:00:00.000000

P3 additions:
- claims, evidence_links tables (WS-1)
- reading_logs, annotations, glossary_terms, knowledge_cards (WS-4)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════
    # P3 WS-1: Claims & Evidence
    # ═══════════════════════════════════════════════════════════════

    op.create_table('claims',
        sa.Column('paper_id', sa.UUID(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('claim_type', sa.String(length=30), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('hedging_level', sa.String(length=20), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('section_ref', sa.String(length=100), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(length=20), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claims_paper_id'), 'claims', ['paper_id'], unique=False)

    op.create_table('evidence_links',
        sa.Column('claim_id', sa.UUID(), nullable=False),
        sa.Column('paper_id', sa.UUID(), nullable=False),
        sa.Column('evidence_type', sa.String(length=20), nullable=False),
        sa.Column('evidence_text', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('strength', sa.String(length=20), nullable=True),
        sa.Column('is_sufficient', sa.Boolean(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id']),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_links_claim_id'), 'evidence_links', ['claim_id'], unique=False)

    # ═══════════════════════════════════════════════════════════════
    # P3 WS-4: Personal Knowledge
    # ═══════════════════════════════════════════════════════════════

    op.create_table('reading_logs',
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('paper_id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=30), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reading_logs_user_id'), 'reading_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_reading_logs_paper_id'), 'reading_logs', ['paper_id'], unique=False)

    op.create_table('annotations',
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('paper_id', sa.UUID(), nullable=False),
        sa.Column('annotation_type', sa.String(length=20), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('page', sa.Integer(), nullable=True),
        sa.Column('position', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_annotations_user_id'), 'annotations', ['user_id'], unique=False)
    op.create_index(op.f('ix_annotations_paper_id'), 'annotations', ['paper_id'], unique=False)

    op.create_table('glossary_terms',
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('term', sa.String(length=200), nullable=False),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.Column('domain', sa.String(length=100), nullable=True),
        sa.Column('source_paper_id', sa.UUID(), nullable=True),
        sa.Column('is_auto_generated', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_paper_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_glossary_terms_user_id'), 'glossary_terms', ['user_id'], unique=False)

    op.create_table('knowledge_cards',
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('paper_id', sa.UUID(), nullable=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('card_type', sa.String(length=20), nullable=False, server_default='concept'),
        sa.Column('difficulty', sa.String(length=10), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('repetition', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ease_factor', sa.Float(), nullable=False, server_default='2.5'),
        sa.Column('interval_days', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('next_review_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_cards_user_id'), 'knowledge_cards', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_knowledge_cards_user_id'), table_name='knowledge_cards')
    op.drop_table('knowledge_cards')
    op.drop_index(op.f('ix_glossary_terms_user_id'), table_name='glossary_terms')
    op.drop_table('glossary_terms')
    op.drop_index(op.f('ix_annotations_paper_id'), table_name='annotations')
    op.drop_index(op.f('ix_annotations_user_id'), table_name='annotations')
    op.drop_table('annotations')
    op.drop_index(op.f('ix_reading_logs_paper_id'), table_name='reading_logs')
    op.drop_index(op.f('ix_reading_logs_user_id'), table_name='reading_logs')
    op.drop_table('reading_logs')
    op.drop_index(op.f('ix_evidence_links_claim_id'), table_name='evidence_links')
    op.drop_table('evidence_links')
    op.drop_index(op.f('ix_claims_paper_id'), table_name='claims')
    op.drop_table('claims')
