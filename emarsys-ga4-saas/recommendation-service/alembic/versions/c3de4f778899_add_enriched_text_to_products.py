"""Add enriched_text to products

Revision ID: c3de4f778899
Revises: b1ef1c111852
Create Date: 2026-03-07 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c3de4f778899'
down_revision: Union[str, Sequence[str], None] = 'b1ef1c111852'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('enriched_text', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'enriched_text')
