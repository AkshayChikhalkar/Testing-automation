"""Rename metadata column to additional_metadata

Revision ID: 779aa8e62590
Revises: 001
Create Date: 2025-10-16 14:59:12.955835

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '779aa8e62590'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the metadata column to additional_metadata
    op.alter_column('data_points', 'metadata', new_column_name='additional_metadata')


def downgrade() -> None:
    # Rename back to metadata
    op.alter_column('data_points', 'additional_metadata', new_column_name='metadata')
