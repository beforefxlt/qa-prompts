"""initial_schema

Revision ID: f24ef6ca4521
Revises: 
Create Date: 2026-03-31 21:14:20.944151

This migration creates the initial schema for the family health record app.
Supports both PostgreSQL and SQLite (development).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f24ef6ca4521'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # member_profiles
    op.create_table(
        'member_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('gender', sa.String(10), nullable=False),
        sa.Column('date_of_birth', sa.Date, nullable=False),
        sa.Column('member_type', sa.String(20), nullable=False),
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_member_profiles_is_deleted', 'member_profiles', ['is_deleted'])

    # document_records
    op.create_table(
        'document_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('member_id', sa.String(36), sa.ForeignKey('member_profiles.id'), nullable=False),
        sa.Column('file_url', sa.String(1024), nullable=False),
        sa.Column('desensitized_url', sa.String(1024), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='uploaded'),
        sa.Column('uploaded_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_document_records_member_id', 'document_records', ['member_id'])
    op.create_index('ix_document_records_status', 'document_records', ['status'])

    # ocr_extraction_results
    op.create_table(
        'ocr_extraction_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('document_records.id'), nullable=False),
        sa.Column('raw_json', sa.JSON, nullable=True),
        sa.Column('processed_items', sa.JSON, nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('rule_conflict_details', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_unique_constraint('uq_ocr_extraction_results_document_id', 'ocr_extraction_results', ['document_id'])

    # review_tasks
    op.create_table(
        'review_tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('document_records.id'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('reviewer_id', sa.String(36), nullable=True),
        sa.Column('audit_trail', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_review_tasks_status', 'review_tasks', ['status'])

    # exam_records
    op.create_table(
        'exam_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('document_records.id'), nullable=False),
        sa.Column('member_id', sa.String(36), sa.ForeignKey('member_profiles.id'), nullable=False),
        sa.Column('exam_date', sa.Date, nullable=False),
        sa.Column('institution_name', sa.String(255), nullable=True),
        sa.Column('baseline_age_months', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_exam_records_member_id', 'exam_records', ['member_id'])

    # observations
    op.create_table(
        'observations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('exam_record_id', sa.String(36), sa.ForeignKey('exam_records.id'), nullable=False),
        sa.Column('metric_code', sa.String(50), nullable=False),
        sa.Column('value_numeric', sa.Float, nullable=True),
        sa.Column('value_text', sa.String(100), nullable=True),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('side', sa.String(10), nullable=True),
        sa.Column('is_abnormal', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('reference_range', sa.String(100), nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=True),
    )
    op.create_index('ix_observations_exam_record_id', 'observations', ['exam_record_id'])
    op.create_index('ix_observations_metric_code', 'observations', ['metric_code'])

    # derived_metrics
    op.create_table(
        'derived_metrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('member_id', sa.String(36), sa.ForeignKey('member_profiles.id'), nullable=False),
        sa.Column('metric_category', sa.String(100), nullable=False),
        sa.Column('value_numeric', sa.Float, nullable=True),
        sa.Column('value_json', sa.JSON, nullable=True),
        sa.Column('algorithm_version', sa.String(50), nullable=True),
        sa.Column('calculation_date', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_derived_metrics_member_id', 'derived_metrics', ['member_id'])
    op.create_index('ix_derived_metrics_category', 'derived_metrics', ['metric_category'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('derived_metrics')
    op.drop_table('observations')
    op.drop_table('exam_records')
    op.drop_table('review_tasks')
    op.drop_table('ocr_extraction_results')
    op.drop_table('document_records')
    op.drop_table('member_profiles')
