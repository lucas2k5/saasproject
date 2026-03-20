"""Add BG/NBD columns: p_alive + expected_transactions to customer_segments

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('customer_segments', sa.Column('p_alive', sa.Float(), nullable=True))
    op.add_column('customer_segments', sa.Column('expected_transactions', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('customer_segments', 'expected_transactions')
    op.drop_column('customer_segments', 'p_alive')
