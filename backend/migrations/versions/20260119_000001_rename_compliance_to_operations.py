"""Rename compliance-focused status values to operations-focused terminology.

This migration transforms the platform from compliance-centric to data operations:
- COMPLIANT → CURRENT
- NON_COMPLIANT → ACTION_REQUIRED
- EXPIRING_SOON → DUE_SOON

Revision ID: 003
Revises: 002
Create Date: 2026-01-19 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename status values from compliance to operations terminology."""
    # Update requirements table status column
    op.execute("""
        UPDATE requirements
        SET status = CASE status
            WHEN 'compliant' THEN 'current'
            WHEN 'non_compliant' THEN 'action_required'
            WHEN 'expiring_soon' THEN 'due_soon'
            ELSE status
        END
        WHERE status IN ('compliant', 'non_compliant', 'expiring_soon')
    """)


def downgrade() -> None:
    """Revert status values back to compliance terminology."""
    op.execute("""
        UPDATE requirements
        SET status = CASE status
            WHEN 'current' THEN 'compliant'
            WHEN 'action_required' THEN 'non_compliant'
            WHEN 'due_soon' THEN 'expiring_soon'
            ELSE status
        END
        WHERE status IN ('current', 'action_required', 'due_soon')
    """)
