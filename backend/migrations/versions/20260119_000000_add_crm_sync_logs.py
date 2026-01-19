"""Add CRM sync logs table for tracking CRM integration operations.

Revision ID: 002
Revises: 001
Create Date: 2026-01-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create crm_sync_logs table
    op.create_table(
        'crm_sync_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('direction', sa.String(20), nullable=False, comment='push or pull'),
        sa.Column('operation', sa.String(50), nullable=False, comment='create, update, delete, compliance_push, test_connection'),
        sa.Column('provider', sa.String(50), nullable=False, comment='hubspot, zapier, salesforce, etc.'),
        sa.Column('external_id', sa.String(255), nullable=True, comment='CRM record ID'),
        sa.Column('request_data', postgresql.JSONB, nullable=False, server_default='{}', comment='Data sent to CRM'),
        sa.Column('response_data', postgresql.JSONB, nullable=False, server_default='{}', comment='Response from CRM'),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('attempt_count', sa.Integer, nullable=False, default=1),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=True, comment='Duration of the sync operation in milliseconds'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for common queries
    op.create_index('ix_crm_sync_logs_account_id', 'crm_sync_logs', ['account_id'])
    op.create_index('ix_crm_sync_logs_entity_id', 'crm_sync_logs', ['entity_id'])
    op.create_index('ix_crm_sync_logs_status', 'crm_sync_logs', ['status'])
    op.create_index('ix_crm_sync_logs_created_at', 'crm_sync_logs', ['created_at'])
    op.create_index('ix_crm_sync_logs_provider', 'crm_sync_logs', ['provider'])


def downgrade() -> None:
    op.drop_index('ix_crm_sync_logs_provider', table_name='crm_sync_logs')
    op.drop_index('ix_crm_sync_logs_created_at', table_name='crm_sync_logs')
    op.drop_index('ix_crm_sync_logs_status', table_name='crm_sync_logs')
    op.drop_index('ix_crm_sync_logs_entity_id', table_name='crm_sync_logs')
    op.drop_index('ix_crm_sync_logs_account_id', table_name='crm_sync_logs')
    op.drop_table('crm_sync_logs')
