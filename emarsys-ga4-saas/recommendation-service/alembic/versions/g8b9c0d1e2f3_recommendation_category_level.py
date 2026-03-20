"""recommendation_category_level column

Revision ID: g8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-03-18

"""
from alembic import op
import sqlalchemy as sa

revision = 'g8b9c0d1e2f3'
down_revision = 'f7a8b9c0d1e2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tenant_configs', sa.Column('recommendation_category_level', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    op.drop_column('tenant_configs', 'recommendation_category_level')
