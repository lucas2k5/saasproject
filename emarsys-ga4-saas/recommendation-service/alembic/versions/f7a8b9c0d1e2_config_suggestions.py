"""config suggestions columns

Revision ID: f7a8b9c0d1e2
Revises: c3d4e5f6a7b8
Create Date: 2026-03-17

"""
from alembic import op
import sqlalchemy as sa

revision = 'f7a8b9c0d1e2'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tenant_configs', sa.Column('config_suggestions', sa.JSON(), nullable=True))
    op.add_column('tenant_configs', sa.Column('suggested_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('tenant_configs', 'suggested_at')
    op.drop_column('tenant_configs', 'config_suggestions')
