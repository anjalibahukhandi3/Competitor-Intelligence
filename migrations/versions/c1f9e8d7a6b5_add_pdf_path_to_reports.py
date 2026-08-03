"""Add pdf_path column to reports table

Revision ID: c1f9e8d7a6b5
Revises: a3f8c1e2b9d4
Create Date: 2026-08-03 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1f9e8d7a6b5'
down_revision: Union[str, Sequence[str], None] = 'a3f8c1e2b9d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pdf_path column to reports table."""
    op.add_column(
        'reports',
        sa.Column(
            'pdf_path',
            sa.String(length=500),
            nullable=True,
            comment='File path to generated PDF report',
        ),
    )


def downgrade() -> None:
    """Remove pdf_path column from reports table."""
    op.drop_column('reports', 'pdf_path')
