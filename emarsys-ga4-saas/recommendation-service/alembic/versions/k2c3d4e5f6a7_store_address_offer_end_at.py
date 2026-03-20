"""Add stores.address and offer_end_at to recommendations

Revision ID: k2c3d4e5f6a7
Revises: j1b2c3d4e5f6
Create Date: 2026-03-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'k2c3d4e5f6a7'
down_revision = 'j1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Store address
    op.add_column('stores', sa.Column('address', sa.String(), nullable=True))

    # offer_end_at on current recommendations
    op.add_column('customer_recommendations_current',
                  sa.Column('offer_end_at', sa.DateTime(timezone=True), nullable=True))

    # offer_end_at on partitioned history table (raw SQL required)
    op.execute("ALTER TABLE customer_recommendations_history ADD COLUMN IF NOT EXISTS offer_end_at TIMESTAMPTZ")


def downgrade() -> None:
    op.execute("ALTER TABLE customer_recommendations_history DROP COLUMN IF EXISTS offer_end_at")
    op.drop_column('customer_recommendations_current', 'offer_end_at')
    op.drop_column('stores', 'address')
