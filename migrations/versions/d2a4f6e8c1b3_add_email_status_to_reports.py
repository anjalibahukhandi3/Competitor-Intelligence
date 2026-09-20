"""Add email_status column to reports table

Revision ID: d2a4f6e8c1b3
Revises: c1f9e8d7a6b5
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2a4f6e8c1b3'
down_revision: Union[str, Sequence[str], None] = 'c1f9e8d7a6b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add email_status column to reports table."""
    op.add_column(
        'reports',
        sa.Column(
            'email_status',
            sa.String(length=20),
            nullable=False,
            server_default='pending',
            comment='Email delivery status: pending | sent | failed',
        ),
    )


def downgrade() -> None:
    """Remove email_status column from reports table."""
    op.drop_column('reports', 'email_status')
